from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from src.utils.llmutils import (
    get_gemini_llm,
    get_claude_llm,
)
from src.utils.constants import FAILURE_RESPONSE

from langchain.output_parsers.structured import ResponseSchema, StructuredOutputParser
import json
from langchain.prompts import (
    FewShotPromptTemplate,
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.example_selectors import (
    SemanticSimilarityExampleSelector,
)
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings


suffix = """Your turn:

    Question: {input}
    SQL Query:
    
    """


def read_examples(path="src/examples/few_shot_queries.json"):
    with open(path, mode="r") as f:
        examples = json.loads(f.read())["examples"]
    return examples


def get_example_selector():
    examples = read_examples()
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        VertexAIEmbeddings(model_name="textembedding-gecko@003"),
        FAISS,
        k=2,
        input_keys=["input"],
    )
    return example_selector


def get_sql_chain(example_selector):
    try:
        llm = get_claude_llm()

        with open("src/prompts/sqlgen_prompt.txt") as f:
            template = f.read()

        few_shot_prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=PromptTemplate.from_template(
                "User input: {input}\nSQL query: {query}"
            ),
            input_variables=["input"],
            prefix=template,
            suffix=suffix,
        )

        full_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate(prompt=few_shot_prompt),
                ("human", "{input}"),
                # MessagesPlaceholder("chat_history"),
            ]
        )

        response_schema = ResponseSchema(
            name="query",
            description="It is the SQL query which is generated based on the users natural language query.",
        )
        output_parser = StructuredOutputParser(response_schemas=[response_schema])
        format_instructions = output_parser.get_format_instructions()

        sql_chain = full_prompt | llm | output_parser
        return sql_chain, format_instructions
    except Exception as e:
        print(f"exception at getting sql chain {e}")


def get_sql_query(user_query, chat_history):
    sql_chain, format_instructions = get_sql_chain(
        example_selector=get_example_selector()
    )
    sql_query_generation_chain = RunnablePassthrough.assign(query=sql_chain)

    print(f"Chat History: \n{chat_history}\n\n")
    sql_query_generation_response = sql_query_generation_chain.invoke(
        {
            "input": user_query,
            "chat_history": chat_history,
            "format_instructions": format_instructions,
        }
    )

    sql_query = sql_query_generation_response["query"]["query"]
    sql_query = sql_query.replace("```", "")
    sql_query = sql_query.replace("sql", "")
    sql_query = sql_query.replace(
        "CLEANED_PUBLIC_EVENTS_DATA", "cleaned_public_events_data"
    )
    sql_query = sql_query.replace("GOOGLE_ADS_DATA", "google_ads_data")
    print(f"SQL Query: \n{sql_query}")
    return sql_query


def get_sql_gen_exception(e):
    print(f"exception at generating sql query {e}")
    sql_query = "Error at generating sql query"
    result = {}
    result["nlp_output"] = FAILURE_RESPONSE
    result["sql_response"] = "N/A"
    return result, sql_query
