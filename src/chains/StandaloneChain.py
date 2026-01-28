from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from src.utils.llmutils import (
    get_gemini_llm,
    get_claude_llm,
)
from src.utils.constants import FAILURE_RESPONSE
from langchain.output_parsers.structured import ResponseSchema, StructuredOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)


def get_standalone_question_chain():
    with open("src/prompts/standalone_prompt.txt") as f:
        contextualize_q_system_prompt = f.read()

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    llm = get_claude_llm()

    standalone_question_chain = RunnablePassthrough.assign(
        final_query=contextualize_q_prompt | llm | StrOutputParser()
    )
    return standalone_question_chain


def get_standalone_question(user_query, chat_history):

    standalone_question_chain = get_standalone_question_chain()
    standalone_question_chain_response = standalone_question_chain.invoke(
        {"input": user_query, "chat_history": chat_history}
    )

    print(f"\n\nStandalone chain response is {standalone_question_chain_response}\n\n")
    standalone_user_query = standalone_question_chain_response["final_query"]
    print(f"Standalone query is {standalone_user_query}\n\n")
    return standalone_user_query


def get_standalone_exception(e):
    print(f"exception at generating standalone question {e}")
    sql_query = "Error at generating standalone question"
    result = {}
    result["nlp_output"] = FAILURE_RESPONSE
    result["sql_response"] = "N/A"
    return result, sql_query
