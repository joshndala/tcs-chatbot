"""
Shared state definitions for the multi-agent system.
"""
from typing import TypedDict, List, Literal, Optional, Any, Annotated
import operator
from dataclasses import dataclass


class Message(TypedDict):
    """Message structure for agent communication."""
    role: Literal["user", "assistant", "system"]
    content: str


from utils.prompts import ACCOUNT_NO_RESULTS, POLICY_NO_RESULTS


def merge_outputs(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """
    Merge two outputs with a newline separator.
    Filters out "No results" messages if one of the outputs is valid content.
    """
    if not left:
        return right
    if not right:
        return left
        
    # Check if either output is a "No results" message
    left_clean = left.strip()
    right_clean = right.strip()
    
    # Loose matching in case of minor formatting differences
    is_left_error = left_clean in [ACCOUNT_NO_RESULTS.strip(), POLICY_NO_RESULTS.strip()]
    is_right_error = right_clean in [ACCOUNT_NO_RESULTS.strip(), POLICY_NO_RESULTS.strip()]
    
    # If one is an error and the other isn't, return the valid one
    if is_left_error and not is_right_error:
        return right
    if is_right_error and not is_left_error:
        return left
        
    return f"{left}\n\n{right}"


class AgentState(TypedDict):
    """
    Shared state for the multi-agent system.
    
    This state is passed between nodes in the LangGraph workflow.
    """
    # Conversation messages
    messages: Annotated[List[Message], operator.add]
    
    # Current user query
    query: str
    
    # Selected agent for handling the query
    agent_type: Optional[Literal["AccountAgent", "PolicyAgent", "Both"]]
    
    # Intermediate results
    sql_query: Optional[str]
    db_results: Optional[List[Any]]
    search_results: Optional[List[str]]
    
    # Final response
    response: Annotated[Optional[str], merge_outputs]
    
    # Error tracking
    error: Annotated[Optional[str], merge_outputs]


@dataclass
class AgentConfig:
    """Configuration for agent behavior."""
    model_name: str = "gemini-3-flash-preview"
    temperature: float = 1.0
    max_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40
