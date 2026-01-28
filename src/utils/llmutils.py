import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from langchain_google_vertexai.model_garden import ChatAnthropicVertex
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_vertexai import VertexAI


def get_gemini_llm():
    gemini_api_key = os.getenv("googleapi_key")
    llm = VertexAI(
        model="gemini-pro",
        google_api_key=gemini_api_key,
        temperature=0.3,
        convert_system_message_to_human=True,
    )
    return llm


def get_claude_llm():
    llm = ChatAnthropicVertex(
        model="claude-3-5-sonnet@20240620",
        temperature=0.3,
        project=os.getenv("PROJECT"),
        location=os.getenv("LOCATION"),
        streaming=True,
    )
    return llm


def get_openai_llm():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo-1106", temperature=0.2, openai_api_key=openai_api_key
    )
    return llm


def convert_to_langchainmsg(session):
    chat_history = []
    for i, k in enumerate(session):
        if i % 2 == 0:
            chat_history.append(HumanMessage(k))
        else:
            chat_history.append(AIMessage(k))
    return chat_history


def convert_to_anthropic_messages(messages):
    chat_history = []
    for i, k in enumerate(messages):
        if i % 2 == 0:
            chat_history.append({"role": "user", "content": k.content})
        else:
            chat_history.append({"role": "assistant", "content": k.content})
    return chat_history


def convert_to_string(messages):
    chat_history = []
    for i, k in enumerate(messages):
        if i % 2 == 0:
            chat_history.append(f"User:   {k.content}")
        else:
            chat_history.append(f"AI:   {k.content}")
    return "\n".join(chat_history)
