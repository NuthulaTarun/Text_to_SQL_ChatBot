import datetime
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from src.utils.llmutils import (
    get_gemini_llm,
    get_claude_llm,
    convert_to_anthropic_messages,
    convert_to_string,
)
from src.utils.constants import FAILURE_RESPONSE
from src.utils.sqlutils import get_result, modified_query
from src.utils.bigqueryutils import (
    get_database,
    get_sql_execution_exception,
    handle_sqlgen_error,
)
from src.chains.NLResponseChain import (
    get_nlp_response_and_plot_columns,
    get_nlp_response_gen_exception,
    get_nlp_model_response,
)
from src.chains.SQLGenChain import (
    get_sql_query,
    get_sql_gen_exception,
    get_example_selector,
)
from src.chains.PlotColumnsChain import get_plot_columns_chain
from src.chains.StandaloneChain import get_standalone_question, get_standalone_exception
from src.chains.IntentRecognitionChain import get_user_intent
from src.MLModels.optimization import get_optimization_results
from src.MLModels.forecasting import get_forecasting_results, process_forecast_results
import os
from dotenv import load_dotenv
import urllib
from langchain.output_parsers.structured import ResponseSchema, StructuredOutputParser
import json
from langchain.prompts import ChatPromptTemplate
from langchain_core.example_selectors import (
    SemanticSimilarityExampleSelector,
)
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.globals import set_debug
from langchain_core.messages import HumanMessage

# set_debug(True)
load_dotenv()

def get_final_response(user_query, chat_history):
    intent = get_user_intent(user_query=user_query)
    if intent["classification"].lower() == "optimization":
        model_results = get_optimization_results()
        print(f"Optimization results: {model_results}")
        model_results.drop(columns=["Expected_revenue"], inplace=True)
        
        result, sql_query = get_nlp_model_response(
            user_query=user_query,
            chat_history=chat_history,
            model_results=model_results,
        )
        
        # converting model results to dict and storing in dict
        result["sql_response"] = model_results.to_dict(orient='records')
        result["intent_type"] = "optimization"
        result["plot_columns"] = "No plot columns"
        print(f"Final optimization response: \n\n {result}\n\n")
    elif intent["classification"].lower() == "forecasting":
        model_name='random_forest'
        start_date='2024-05-30'
        
        # Dynamically set forecast_start_date to today's date
        forecast_start_date = datetime.date.today()

        # Set forecast_end_date to 2 weeks from today
        forecast_end_date = forecast_start_date + datetime.timedelta(weeks=2)

        # Convert dates to strings
        forecast_start_date = forecast_start_date.strftime("%Y-%m-%d")
        forecast_end_date = forecast_end_date.strftime("%Y-%m-%d")
        feature=intent['feature']
        print('forecast start date:',forecast_start_date)
        model_results = get_forecasting_results(model_name,start_date,forecast_start_date,forecast_end_date,feature)
        print('model_results:',model_results)
        result, sql_query = get_nlp_model_response(
            user_query=user_query,
            chat_history=chat_history,
            model_results=model_results,
        )
        
        model_results = process_forecast_results(model_results, feature)
        result["sql_response"] = model_results.to_dict(orient='records')
        result["intent_type"] = "forecasting"
        result["plot_columns"] = "No plot columns"
    else:
        result, sql_query = get_response(
            user_query=user_query, chat_history=chat_history
        )
    return result, sql_query


def get_response(user_query: str, chat_history: list, db=get_database()):
    # 1. Get standalone question
    try:
        standalone_user_query = get_standalone_question(
            user_query=user_query, chat_history=chat_history
        )
        print(f"Standalone query is {standalone_user_query}\n\n")
    except Exception as e:
        result, sql_query = get_standalone_exception(e)
        result["intent_type"] = "analytics"
        return result, sql_query

    # 2. Getting sql query
    try:
        generated_sql_query = get_sql_query(
            user_query=standalone_user_query, chat_history=chat_history
        )
        print(f"SQL query is {generated_sql_query}\n\n")
    except Exception as e:
        result, sql_query = get_sql_gen_exception(e)
        result["intent_type"] = "analytics"

    # 3. Executing query to get sql response
    attempt_limit = 3
    attempts = 0
    while attempts < attempt_limit:
        try:
            sql_response = get_result(query=generated_sql_query)
            print(f"sql response is {sql_response}\n\n")

            if len(sql_response) < 1:
                result = {}
                result["nlp_output"] = """No data is present for this requirement."""
                result["sql_response"] = "N/A"
                result["intent_type"] = "analytics"
                return result, generated_sql_query
            break
        except Exception as e:
            generated_sql_query, attempts = handle_sqlgen_error(
                e=e,
                attempts=attempts,
                user_query=user_query,
                chat_history=chat_history,
                example_selector=get_example_selector(),
                sql_query = generated_sql_query,
            )
    else:
        result, sql_query = get_sql_execution_exception()
        result["intent_type"] = "analytics"
        return result, sql_query

    # 4.Generating nlp response from sql response
    try:
        result, sql_query = get_nlp_response_and_plot_columns(
            user_query=standalone_user_query,
            sql_query=generated_sql_query,
            chat_history=chat_history,
            sql_response = sql_response,
        )
    except Exception as e:
        result, sql_query = get_nlp_response_gen_exception(e)
    result["intent_type"] = "analytics"
    
    return result, sql_query