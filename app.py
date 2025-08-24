# app.py
import streamlit as st
from langchain_core.messages import HumanMessage
from agent.graph import create_newspaper_agent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="The Daily Agent 📰", layout="wide")

st.title("The Daily Agent 📰")
st.subheader("Your AI-Powered Newspaper, Generated on Demand")

# --- AGENT INITIALIZATION ---
# Using st.cache_resource ensures the graph is created only once
@st.cache_resource
def get_agent_graph():
    """Creates and returns the compiled newspaper agent graph."""
    # Ensure API keys are available
    if not os.getenv("GROQ_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        st.error("API keys for Groq and Tavily not found. Please set them in your .env file.")
        return None
    return create_newspaper_agent()

graph = get_agent_graph()

# --- USER INTERACTION ---
if graph:
    user_request = st.text_input(
        "What news are you interested in today?",
        placeholder="e.g., 'Generate today's newspaper' or 'Tell me about AI and Formula 1'"
    )

    if st.button("Generate Newspaper"):
        if not user_request:
            st.warning("Please enter a request to generate your newspaper.")
        else:
            initial_input = {"messages": [HumanMessage(content=user_request)]}
            st.markdown("---")
            
            with st.spinner("🤖 The Daily Agent is writing your newspaper... This may take a moment."):
                final_response = None
                with st.expander("Show Agent Thoughts 🧠"):
                    for event in graph.stream(initial_input, stream_mode="values", config={"recursion_limit": 50}):
                        if "messages" in event and event["messages"]:
                            latest_message = event["messages"][-1]
                            if hasattr(latest_message, 'content') and latest_message.content:
                                st.write(f"**Step: {type(latest_message).__name__}**")
                                st.write(latest_message.content)
                                st.write("---")
                        final_response = event

            st.markdown("---")
            st.header("Your Newspaper Is Ready! 🗞️")
            
            if final_response and final_response.get("final_output"):
                st.markdown(final_response["final_output"])
            else:
                st.error("Sorry, the agent finished but a newspaper could not be generated.")