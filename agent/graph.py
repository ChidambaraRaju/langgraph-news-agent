# agent/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

# Import from local package files
from .state import AgentState
from .nodes import (
    input_parser_node, 
    supervisor_node, 
    search_agent_node, 
    summarizer_node, 
    newspaper_creator_node,
    tools  # Import the tools list from nodes.py
)

def create_newspaper_agent():
    """Builds and compiles the LangGraph agent."""
    builder = StateGraph(AgentState)
    
    # Add Nodes
    builder.add_node("input_parser", input_parser_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("search_agent", search_agent_node)
    builder.add_node("tool_executor", ToolNode(tools))
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("newspaper_creator", newspaper_creator_node)
    
    # Define Edges
    builder.add_edge(START, "input_parser")
    builder.add_edge("input_parser", "supervisor")

    def supervisor_condition(state: AgentState):
        if "Finishing" in state['messages'][-1].content:
            return "newspaper_creator"
        return "search_agent"

    builder.add_conditional_edges("supervisor", supervisor_condition, {
        "newspaper_creator": "newspaper_creator",
        "search_agent": "search_agent"
    })
    
    builder.add_conditional_edges("search_agent", tools_condition, {
        "tools": "tool_executor",
        "__end__": "summarizer"
    })
    
    builder.add_edge("tool_executor", "search_agent")
    builder.add_edge("summarizer", "supervisor")
    builder.add_edge("newspaper_creator", END)
    
    return builder.compile()