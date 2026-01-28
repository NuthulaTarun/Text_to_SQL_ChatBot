from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from src.utils.llmutils import (
    get_gemini_llm,
    get_claude_llm,
)
from src.utils.constants import FAILURE_RESPONSE
from src.utils.sqlutils import get_result, modified_query
from src.utils.bigqueryutils import get_database
import os
from dotenv import load_dotenv
import urllib
from langchain.output_parsers.structured import ResponseSchema, StructuredOutputParser
import json
from langchain.prompts import (
    FewShotPromptTemplate,
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.example_selectors import (
    SemanticSimilarityExampleSelector,
)
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.globals import set_debug
from langchain_core.messages import HumanMessage

def get_plot_columns_chain(user_query, sql_response):
    llm = get_claude_llm()
    with open("src/prompts/plotcolumns_prompt.txt") as f:
        template = f.read()
    
    response_schema = ResponseSchema(
        name="plot_columns",
        description="It is the list of columns which are generated based on the users natural language query.",
    )
    plot_columns_output_parser = StructuredOutputParser(response_schemas=[response_schema])
    plot_columns_format_instructions = plot_columns_output_parser.get_format_instructions() 
    
    plot_columns_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            ("human", "{input}"),
        ]
    )
    
    plot_columns_chain = RunnablePassthrough.assign(
        plot_columns_query=plot_columns_q_prompt | llm
    )

    return plot_columns_chain, plot_columns_format_instructions, plot_columns_output_parser