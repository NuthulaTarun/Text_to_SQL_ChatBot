import os
from langchain_community.utilities import SQLDatabase
from src.utils.sqlutils import get_result, modified_query
from src.chains.SQLGenChain import get_sql_chain, get_example_selector, get_sql_query
from src.utils.constants import FAILURE_RESPONSE
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv


load_dotenv()


def get_database() -> SQLDatabase:
    sqlalchemy_url = f"bigquery://{os.getenv('PROJECT')}/{os.getenv('DATASET_POC')}?credentials_path=credentials.json"
    print(sqlalchemy_url)
    db = SQLDatabase.from_uri(sqlalchemy_url)
    return db


def handle_sqlgen_error(
    e, attempts, user_query, chat_history, example_selector, sql_query
):
    print(f"An error occurred at executing sql query: {str(e)}")
    for error in e.errors:
        if "unrecognized name" in error["message"].lower():
            print(f"sql_query is {sql_query}\n\n")
            sql_query = modified_query(
                query=sql_query,
                project_id=os.getenv("PROJECT"),
                dataset_id=os.getenv("DATASET_POC"),
            )

            attempts += 1
            print(f"Modified sql_query at attempt {attempts} is:\n\n {sql_query}\n\n")
        else:
            sql_chain, format_instructions = get_sql_chain(
                chat_history=chat_history,
                example_selector=example_selector,
            )

            sql_query_generation_chain = RunnablePassthrough.assign(query=sql_chain)
            sql_query_generation_response = sql_query_generation_chain.invoke(
                {
                    "input": user_query,
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
            print(f"sql_query is {sql_query}\n\n")
            attempts += 1
            print(f"modified sql_query at attempt {attempts} is {sql_query}\n\n")
    return sql_query, attempts


def execute_sql_query(user_query, chat_history):
    # 3. Executing query to get sql response
    attempt_limit = 3
    attempts = 0
    while attempts < attempt_limit:
        try:
            sql_response = get_result(query=sql_query)
            print(f"sql response is {sql_response}\n\n")

            if len(sql_response) < 1:
                result = {}
                result["nlp_output"] = """No data is present for this requirement."""
                result["sql_response"] = "N/A"
                return result, sql_query
            break
        except Exception as e:
            print(f"An error occurred at executing sql query: {str(e)}")
            for error in e.errors:
                if "unrecognized name" in error["message"].lower():
                    print(f"sql_query is {sql_query}\n\n")
                    sql_query = modified_query(
                        query=sql_query,
                        project_id=os.getenv("PROJECT"),
                        dataset_id=os.getenv("DATASET_POC"),
                    )

                    attempts += 1
                    print(
                        f"Modified sql_query at attempt {attempts} is:\n\n {sql_query}\n\n"
                    )
                else:
                    sql_query = get_sql_query(
                        user_query=user_query, chat_history=chat_history
                    )
                    print(f"sql_query is {sql_query}\n\n")
                    attempts += 1
                    print(
                        f"modified sql_query at attempt {attempts} is {sql_query}\n\n"
                    )


def get_sql_execution_exception():
    print("Exception at executing sql query")
    sql_query = "Exception at executing sql query"
    result = {}
    result["nlp_output"] = FAILURE_RESPONSE
    result["sql_response"] = "N/A"
    return result, sql_query
