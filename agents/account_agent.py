"""
AccountAgent: Specialized agent for SQL-based customer account queries.
Handles customer information, policy details, and claim status.
"""
import json
from typing import Dict, Any
from google import genai
from google.genai import types
from config.settings import settings
from database.sqlite_manager import db_manager
from utils.prompts import (
    ACCOUNT_AGENT_PROMPT,
    ACCOUNT_RESPONSE_PROMPT,
    ERROR_PROMPT,
    ACCOUNT_NO_RESULTS
)
from agents.state import AgentState, AgentConfig


class AccountAgent:
    """Agent specialized in handling SQL-based account queries."""
    
    def __init__(self, config: AgentConfig = None):
        """
        Initialize the AccountAgent.
        
        Args:
            config: Agent configuration (uses defaults if not provided)
        """
        self.config = config or AgentConfig()
        
        # Configure Gemini Client
        self.client = genai.Client(api_key=settings.google_api_key)
        
        # Generate Content Config
        self.generation_config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE"
                )
            ]
        )
        
        # Initialize dynamic context lazily
        self.db_context = ""

    def _get_db_context(self) -> str:
        """Dynamically fetch distinct values for categorical columns."""
        if self.db_context:
            return self.db_context
            
        try:
            print("🔄 Fetching DB context...")
            context = ["\nCurrent Database Values (Use these EXACT strings):"]
            
            # Columns to inspect
            columns = {
                'ticket_priority': 'tickets',
                'ticket_status': 'tickets',
                'ticket_type': 'tickets',
                'ticket_channel': 'tickets',
                'product_purchased': 'customers'
            }
            
            for col, table in columns.items():
                query = f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL ORDER BY {col}"
                results = db_manager.execute_query(query)
                values = [str(row[col]) for row in results if row.get(col)]
                if values:
                    # Limit to top 20 to avoid context overflow if many values
                    val_str = ", ".join([f"'{v}'" for v in values[:20]])
                    context.append(f"- {col}: {val_str}")
            
            self.db_context = "\n".join(context)
            print(f"✅ DB Context loaded ({len(self.db_context)} chars)")
            return self.db_context
        except Exception as e:
            print(f"Warning: Could not fetch DB context: {e}")
            return ""

    def generate_sql(self, query: str) -> str:
        """
        Generate SQL query from natural language.
        
        Args:
            query: User's natural language question
            
        Returns:
            Generated SQL query string
        """
        # Ensure context is loaded
        context = self._get_db_context()
        
        # Inject dynamic context into the prompt
        raw_prompt = ACCOUNT_AGENT_PROMPT
        if "{query}" in raw_prompt:
             # Basic injection if currently parameterized
             full_prompt = raw_prompt.replace("{query}", f"{context}\n\nUser Question: {query}")
        else:
             full_prompt = f"{raw_prompt}\n{context}\n\nUser Question: {query}"

        print(f"🤖 Generating SQL for: {query}")
        response = self.client.models.generate_content(
            model=self.config.model_name,
            contents=full_prompt,
            config=self.generation_config
        )
        
        sql_query = ""
        if response and hasattr(response, 'text') and response.text:
            sql_query = response.text.strip()
        else:
            # Fallback or error handling
            print(f"Warning: Empty response from model. Response: {response}")
            return ""
        
        # Clean up the SQL query
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        print(f"   ⏩ SQL: {sql_query}")
        
        return sql_query
    
    def execute_query(self, sql_query: str) -> list:
        """
        Execute SQL query safely.
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            Query results as list of dictionaries
        """
        if not sql_query:
            return []
            
        try:
            results = db_manager.execute_query(sql_query)
            return results
        except Exception as e:
            raise Exception(f"SQL execution error: {str(e)}")
    
    def format_response(self, query: str, results: list) -> str:
        """
        Format database results into a natural language response.
        
        Args:
            query: Original user query
            results: Database query results
            
        Returns:
            Formatted natural language response
        """
        if not results:
            return ACCOUNT_NO_RESULTS
        
        # Convert results to readable format
        results_text = json.dumps(results, indent=2, default=str)
        
        prompt = ACCOUNT_RESPONSE_PROMPT.format(
            query=query,
            results=results_text
        )
        
        response = self.client.models.generate_content(
            model=self.config.model_name,
            contents=prompt,
            config=self.generation_config
        )
        
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        return "I apologize, but I couldn't generate a response."
    
    def process(self, state: AgentState) -> AgentState:
        """
        Process a user query through the AccountAgent workflow.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with results
        """
        try:
            query = state['query']
            
            # Step 1: Generate SQL query
            sql_query = self.generate_sql(query)
            
            # Step 2: Execute query
            results = self.execute_query(sql_query)
            
            # Step 3: Format response
            response = self.format_response(query, results)
            
            # Return partial update
            return {
                "sql_query": sql_query,
                "db_results": results,
                "response": response,
                "messages": [{
                    'role': 'assistant',
                    'content': response
                }]
            }
            
        except Exception as e:
            error_message = ERROR_PROMPT.format(error=str(e))
            return {
                "error": str(e),
                "response": error_message,
                "messages": [{
                    'role': 'assistant',
                    'content': error_message
                }]
            }
    
    def query_customer_by_name(self, name: str) -> Dict[str, Any]:
        """
        Helper method: Query customer by name.
        
        Args:
            name: Customer name
            
        Returns:
            Customer information
        """
        customers = db_manager.get_customer_by_name(name)
        return customers
    
    def query_policies_by_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Helper method: Get all policies for a customer.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List of policies
        """
        policies = db_manager.get_policies_by_customer_id(customer_id)
        return policies
    
    def query_claims_by_policy(self, policy_id: int) -> Dict[str, Any]:
        """
        Helper method: Get all claims for a policy.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            List of claims
        """
        claims = db_manager.get_claims_by_policy_id(policy_id)
        return claims


# Global agent instance
account_agent = AccountAgent()
