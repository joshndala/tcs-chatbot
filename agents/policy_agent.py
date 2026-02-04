"""
PolicyAgent: Specialized agent for RAG-based policy document retrieval.
Handles questions about policy terms, coverage, and benefits.
"""
from typing import List, Dict, Any
from typing import List, Dict, Any
from google import genai
from google.genai import types
from config.settings import settings
from database.vector_store import vector_store
from utils.prompts import (
    POLICY_AGENT_PROMPT,
    ERROR_PROMPT,
    POLICY_NO_RESULTS,
    SYSTEM_PROMPT
)
from agents.state import AgentState, AgentConfig


class PolicyAgent:
    """Agent specialized in RAG-based policy document queries."""
    
    def __init__(self, config: AgentConfig = None):
        """
        Initialize the PolicyAgent.
        
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
            system_instruction=SYSTEM_PROMPT,
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
    
    def retrieve_context(self, query: str, n_results: int = 3) -> List[str]:
        """
        Retrieve relevant document chunks from vector store.
        
        Args:
            query: User's question
            n_results: Number of relevant chunks to retrieve
            
        Returns:
            List of relevant document chunks
        """
        try:
            results = vector_store.search(query, n_results=n_results)
            
            # Extract documents from results
            documents = results.get('documents', [])
            metadatas = results.get('metadatas', [])
            
            # Format context with metadata
            formatted_chunks = []
            for doc, meta in zip(documents, metadatas):
                filename = meta.get('filename', 'Unknown')
                chunk_info = f"[Source: {filename}]\n{doc}"
                formatted_chunks.append(chunk_info)
            
            return formatted_chunks
            
        except Exception as e:
            raise Exception(f"Vector search error: {str(e)}")
    
    def generate_response(self, query: str, context: List[str]) -> str:
        """
        Generate response using retrieved context.
        
        Args:
            query: User's question
            context: Retrieved document chunks
            
        Returns:
            Generated response
        """
        if not context:
            return POLICY_NO_RESULTS
        
        # Combine context chunks
        context_text = "\n\n".join(context)
        
        # Generate response
        prompt = POLICY_AGENT_PROMPT.format(
            query=query,
            context=context_text
        )
        
        response = self.client.models.generate_content(
            model=self.config.model_name,
            contents=prompt,
            config=self.generation_config
        )
        
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        return "I apologize, but I couldn't generate a response based on the policy documents."
    
    def process(self, state: AgentState) -> AgentState:
        """
        Process a user query through the PolicyAgent workflow.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with results
        """
        try:
            query = state['query']
            
            # Step 1: Retrieve relevant context
            context_chunks = self.retrieve_context(query, n_results=5)
            
            # Step 2: Generate response
            response = self.generate_response(query, context_chunks)
            
            # Return partial update
            return {
                "search_results": context_chunks,
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
    
    def search_specific_document(
        self,
        query: str,
        filename: str,
        n_results: int = 3
    ) -> List[str]:
        """
        Search within a specific policy document.
        
        Args:
            query: Search query
            filename: Specific document to search
            n_results: Number of results to return
            
        Returns:
            List of relevant chunks from the specified document
        """
        try:
            results = vector_store.search_by_filename(
                query=query,
                filename=filename,
                n_results=n_results
            )
            
            return results.get('documents', [])
            
        except Exception as e:
            raise Exception(f"Document search error: {str(e)}")
    
    def get_document_summary(self, filename: str) -> str:
        """
        Generate a summary of a policy document.
        
        Args:
            filename: Document filename
            
        Returns:
            Summary of the document
        """
        try:
            # Retrieve first few chunks to get overview
            results = vector_store.search_by_filename(
                query="summary overview main points",
                filename=filename,
                n_results=3
            )
            
            chunks = results.get('documents', [])
            
            if not chunks:
                return f"No content found for {filename}"
            
            # Generate summary using Gemini
            context = "\n\n".join(chunks)
            prompt = f"""Provide a brief summary of this insurance policy document:

{context}

Summary:"""
            
            response = self.model.generate_content(prompt)
            
            # Properly handle Gemini 3 content blocks
            return response.text.strip() if hasattr(response, 'text') else str(response).strip()
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"


# Global agent instance
policy_agent = PolicyAgent()
