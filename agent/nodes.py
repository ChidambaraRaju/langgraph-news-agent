# agent/nodes.py

from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime

# Import from local package files
from .state import AgentState, Summaries, ParsedRequest, ArticleSummary
from config import GENERAL_TOPICS, MAIN_LLM_MODEL, NEWSPAPER_CREATOR_LLM_MODEL

# Import LLMs and Tools here to be used by nodes
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

import os
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


llm = ChatGroq(model=MAIN_LLM_MODEL, api_key=GROQ_API_KEY)
llm_for_newspaper_creation = ChatGroq(model=NEWSPAPER_CREATOR_LLM_MODEL, api_key=GROQ_API_KEY)

search_tool = TavilySearch(max_results=3, api_key=TAVILY_API_KEY)
tools = [search_tool]
llm_with_tool = llm.bind_tools(tools)


# --- NODE FUNCTIONS ---

def input_parser_node(state: AgentState):
    user_message = state['messages'][-1].content
    intent_llm = llm.with_structured_output(ParsedRequest)
    prompt = f"""
    Analyze the user's request below. Your task is to determine two things:
    1.  Does the request include a general ask for the news (e.g., "get today's news", "daily newspaper")?
    2.  Does the request mention any specific topics (e.g., "Formula 1", "AI developments")?
    Return the structured analysis based on this.
    User Request: "{user_message}"
    """
    parsed_request = intent_llm.invoke(prompt)
    
    final_topics = set()
    if parsed_request.includes_general_news:
        final_topics.update(GENERAL_TOPICS)
    if parsed_request.specific_topics:
        final_topics.update(parsed_request.specific_topics)
    if not final_topics:
         final_topics.update(GENERAL_TOPICS)

    return {"topics_to_process": list(final_topics)}


def supervisor_node(state: AgentState):
    if state['topics_to_process']:
        next_topic = state['topics_to_process'][0]
        remaining_topics = state['topics_to_process'][1:]
        # Get today's date to make the search timely.
        today_date = datetime.now().strftime("%B %d, %Y")
        
        # Update the instruction to be specific about the date.
        instruction = HumanMessage(
            content=f"""
            Your task is to find relevant news articles published on or around today's date, {today_date}, on the topic: '{next_topic}'.

            Use your search tool to find the top 3-4 most relevant articles from the last few days. Then, compile the search results into a single block of text for the summarizer.
            """
        )
        return {
            "messages": [instruction],
            "topics_to_process": remaining_topics,
            "current_topic": next_topic
        }
    else:
        return {"messages": [HumanMessage(content="All topics processed. Finishing.")]}


def search_agent_node(state: AgentState):
    response = llm_with_tool.invoke(state['messages'])
    return {"messages": [response]}


def summarizer_node(state: AgentState):
    last_message = state['messages'][-1].content
    parser = PydanticOutputParser(pydantic_object=Summaries)
    prompt_template = ChatPromptTemplate.from_template(
        """
        You are an expert news analyst. Your task is to take the provided text
        and convert it into a DETAILED, well-structured summary.
        The summary should ideally be at least 2-3 paragraphs long and cover background, the main event, and implications.
        **CRITICAL INSTRUCTION:** If the provided "Raw Data" is too sparse, create a shorter, one-paragraph summary based only on the information you have. Do NOT invent information.
        Extract the title and URL, and generate the summary.
        {format_instructions}
        Raw Data: {raw_data}
        """,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt_template | llm | parser
    summary_object = chain.invoke({"raw_data": last_message})
    current_topic = state['current_topic']
    existing_digests = state.get("completed_digests", {})
    existing_digests[current_topic] = summary_object.articles
    return {"completed_digests": existing_digests}


def newspaper_creator_node(state: AgentState):
    all_digests = state["completed_digests"]
    user_message = state['messages'][0].content
    today_date = datetime.now().strftime("%B %d, %Y")
    formatted_digests = ""
    for topic, summaries in all_digests.items():
        formatted_digests += f"--- Section: {topic} ---\\n\\n"
        for summary in summaries:
            formatted_digests += f"Title: {summary.title}\\n"
            if summary.url:
                formatted_digests += f"Source: {summary.url}\\n"
            formatted_digests += f"Summary:\\n{summary.summary}\\n\\n"
    prompt = f"""
    You are the Editor-in-Chief of "The Daily Agent," a futuristic, AI-powered newspaper.
    Your task is to take today's compiled news summaries and create the **full newspaper edition** for today, {today_date}.
    The user's original request was: "{user_message}".

    ### INSTRUCTIONS FOR WRITING:
    1. **Masthead & Lead Story**
    - Begin with the newspaper's name, "The Daily Agent," and today's date.
    - Create a bold, engaging front-page headline and opening story that captures the biggest overall theme of the day.

    2. **Editor's Note**
    - Write a short 2-3 paragraph introduction from the editor summarizing the mood, themes, or unique focus of this edition.

    3. **Featured Stories (If Applicable)**
    - If the user's original request referenced specific topics, highlight those stories first in a section titled “Today's Featured Stories.”
    - Expand each featured summary into a **full article (3-5 paragraphs)** with engaging detail, background, and implications.

    4. **Standard Newspaper Sections**
    Organize the rest of the content into clearly labeled sections such as:
    - World News
    - Politics
    - Business & Economy
    - Technology
    - Science & Health
    - Culture & Entertainment
    - Sports
    - Opinion / Editorial
    - Lifestyle (optional, if content allows)

    Each section should contain **at least one or two fully written articles**, each 2-5 paragraphs long.

    5. **Article Writing Style**
    - Treat each summary as **raw reporting notes**. Expand it into a polished article.
    - Provide context, analysis, and narrative flow.  
    - Add **imagined expert commentary, public reaction, or illustrative details** where appropriate.  
    - Each article should read like a real newspaper piece, not a short blurb.

    6. **Tone & Presentation**
    - Use professional, engaging, and highly readable journalistic style.  
    - Write in clear prose with varied sentence structure.  
    - Maintain objectivity, but allow editorial voice in the **Opinion** and **Editor's Note** sections.

    ### SOURCE MATERIAL:
    The following compiled news summaries are your reporter's notes:
    {formatted_digests}

    Now, generate the **entire issue of "The Daily Agent"**, formatted as a full newspaper with multiple sections and complete articles.
    """
    newspaper_content = llm_for_newspaper_creation.invoke(prompt).content
    return {"final_output": newspaper_content}