"""
LangGraph workflow for multi-agent orchestration.
Implements router and agent nodes with conditional routing.
"""
from typing import Literal
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END
from config.settings import settings
from agents.state import AgentState, AgentConfig
from agents.account_agent import account_agent
from agents.policy_agent import policy_agent
from utils.prompts import ROUTER_PROMPT, SYSTEM_PROMPT


class MultiAgentGraph:
    """LangGraph workflow for multi-agent system."""
    
    def __init__(self):
        """Initialize the multi-agent graph."""
        # Configure Gemini Client for routing
        self.client = genai.Client(api_key=settings.google_api_key)
        
        self.router_config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
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
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self.router_node)
        workflow.add_node("account_agent", self.account_agent_node)
        workflow.add_node("policy_agent", self.policy_agent_node)
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Add conditional edges from router
        workflow.add_conditional_edges(
            "router",
            self.route_query,
            {
                "AccountAgent": "account_agent",
                "PolicyAgent": "policy_agent",
            }
        )
        
        # Add edges to END
        workflow.add_edge("account_agent", END)
        workflow.add_edge("policy_agent", END)
        
        # Compile graph
        return workflow.compile()
    
    def router_node(self, state: AgentState) -> AgentState:
        """
        Router node: Classifies the query and determines which agent to use.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with agent_type set
        """
        query = state['query']
        
        # Generate classification
        prompt = ROUTER_PROMPT.format(query=query)
        
        response = self.client.models.generate_content(
            model=settings.model_name,
            contents=prompt,
            config=self.router_config
        )
        
        agent_type = "PolicyAgent" # Default fallback
        # Properly handle Gemini 3 content blocks - use .text property
        response_text = ""
        if response and hasattr(response, 'text') and response.text:
             response_text = response.text.strip()
        
        # Parse Chain-of-Thought response
        agent_type = "PolicyAgent" # Default
        
        # 1. Look for explicit classification line
        if "Classification: AccountAgent" in response_text:
            agent_type = "AccountAgent"
        elif "Classification: PolicyAgent" in response_text:
            agent_type = "PolicyAgent"
        # 2. Key phrase fallback
        elif "AccountAgent" in response_text:
             agent_type = "AccountAgent"
        
        # Update state
        state['agent_type'] = agent_type
        
        return state
    
    def route_query(self, state: AgentState) -> Literal["AccountAgent", "PolicyAgent"]:
        """
        Routing function for conditional edges.
        
        Args:
            state: Current agent state
            
        Returns:
            Agent type to route to
        """
        return state['agent_type']
    
    def account_agent_node(self, state: AgentState) -> AgentState:
        """
        AccountAgent node: Processes account-related queries.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with results
        """
        return account_agent.process(state)
    
    def policy_agent_node(self, state: AgentState) -> AgentState:
        """
        PolicyAgent node: Processes policy document queries.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with results
        """
        return policy_agent.process(state)
    
    def run(self, query: str, messages: list = None) -> AgentState:
        """
        Run the multi-agent workflow.
        
        Args:
            query: User's question
            messages: Conversation history (optional)
            
        Returns:
            Final agent state with response
        """
        # Initialize state
        initial_state: AgentState = {
            'messages': messages or [],
            'query': query,
            'agent_type': None,
            'sql_query': None,
            'db_results': None,
            'search_results': None,
            'response': None,
            'error': None
        }
        
        # Add user message
        initial_state['messages'].append({
            'role': 'user',
            'content': query
        })
        
        # Run graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state
    
    def stream(self, query: str, messages: list = None):
        """
        Stream the multi-agent workflow execution.
        
        Args:
            query: User's question
            messages: Conversation history (optional)
            
        Yields:
            State updates as they occur
        """
        # Initialize state
        initial_state: AgentState = {
            'messages': messages or [],
            'query': query,
            'agent_type': None,
            'sql_query': None,
            'db_results': None,
            'search_results': None,
            'response': None,
            'error': None
        }
        
        # Add user message
        initial_state['messages'].append({
            'role': 'user',
            'content': query
        })
        
        # Stream graph execution
        for state in self.graph.stream(initial_state):
            yield state


# Global graph instance
multi_agent_graph = MultiAgentGraph()
