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


def get_userintent_example_selector(
    examples_path="src/examples/intent_trial.json",
):
    with open(examples_path, mode="r") as f:
        examples = json.loads(f.read())["examples"]

    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        VertexAIEmbeddings(model_name="textembedding-gecko@003"),
        FAISS,
        k=2,
        input_keys=["input"],
    )
    return example_selector


def get_user_intent_chain():

    with open("src/prompts/userintent_prompt.txt") as f:
        template = f.read()

    suffix = """Your turn:

        User question: {input}
        Classification:
        objective:
        duration:
        feature:
        
        """

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=get_userintent_example_selector(),
        example_prompt=PromptTemplate.from_template(
            "User input: {input}\nClassification: {classification}\nobjective:{objective}\nduration:{duration}\nfeature{feature}"
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

    response_schema = [ResponseSchema(name="classification", description="It is the category in which the user query is classified."),
        ResponseSchema(name="objective", description="It is the objective of the user query."),
        ResponseSchema(name="duration", description="The duration mentioned in the user query, if any."),
        ResponseSchema(name="feature", description="column name to forecast the data."),   
    ]
    output_parser = StructuredOutputParser(response_schemas=response_schema)
    format_instructions = output_parser.get_format_instructions()

    llm = get_claude_llm()
    intent_classification_chain = full_prompt | llm | output_parser
    return intent_classification_chain, format_instructions


def get_user_intent(user_query):
    intent_classification_chain, format_instructions = get_user_intent_chain()
    intent_recognition_chain = RunnablePassthrough.assign(
        category=intent_classification_chain
    )

    user_intent = intent_recognition_chain.invoke(
        input={"input": user_query, "format_instructions": format_instructions}
    )["category"]
    print(user_intent)
    
    # Accessing individual elements of the user_intent dictionary
    classification = user_intent["classification"]
    objective = user_intent["objective"]
    duration = user_intent["duration"]
    feature = user_intent["feature"]

    return {"classification": classification, "objective": objective, "duration": duration,"feature":feature}