"""
Shared state definitions for the multi-agent system.
"""
from typing import TypedDict, List, Literal, Optional, Any
from dataclasses import dataclass


class Message(TypedDict):
    """Message structure for agent communication."""
    role: Literal["user", "assistant", "system"]
    content: str


class AgentState(TypedDict):
    """
    Shared state for the multi-agent system.
    
    This state is passed between nodes in the LangGraph workflow.
    """
    # Conversation messages
    messages: List[Message]
    
    # Current user query
    query: str
    
    # Selected agent for handling the query
    agent_type: Optional[Literal["AccountAgent", "PolicyAgent"]]
    
    # Intermediate results
    sql_query: Optional[str]
    db_results: Optional[List[Any]]
    search_results: Optional[List[str]]
    
    # Final response
    response: Optional[str]
    
    # Error tracking
    error: Optional[str]


@dataclass
class AgentConfig:
    """Configuration for agent behavior."""
    model_name: str = "gemini-3-flash-preview"
    temperature: float = 1.0
    max_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40
