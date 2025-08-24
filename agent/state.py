# agent/state.py

from typing import Annotated, TypedDict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

# --- Pydantic Models for Structured Data ---

class ArticleSummary(BaseModel):
    """A structured container for a single article's summary."""
    title: str = Field(description="The main headline of the news article.")
    url: Optional[str] = Field(description="The direct web link to the original article. Can be None if not found.")
    summary: str = Field(description="A detailed, AI-generated summary of the article.")

class Summaries(BaseModel):
    """A container for a list of article summaries."""
    articles: List[ArticleSummary]

class ParsedRequest(BaseModel):
    """A model to represent the parsed user request."""
    includes_general_news: bool = Field(
        description="Set to true if the user makes a general request for the newspaper or 'today's news'."
    )
    specific_topics: List[str] = Field(
        default=[],
        description="A list of specific news topics the user explicitly mentioned."
    )

# --- The Graph's State ---

class AgentState(TypedDict):
    """
    Represents the state of the news digest agent's workflow.

    Attributes:
        messages: The history of the conversation.
        topics_to_process: A queue of topic strings to be researched.
        completed_digests: A dictionary mapping topics to their summaries.
        current_topic: The topic currently being researched.
        final_output: The final, polished newspaper content.
    """
    messages: Annotated[list[AnyMessage], add_messages]
    topics_to_process: List[str]
    completed_digests: dict[str, List[ArticleSummary]]
    current_topic: str
    final_output: Optional[str]