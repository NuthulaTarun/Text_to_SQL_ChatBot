import streamlit as st
import pandas as pd
import plotly.express as px
from src.chatbot_ui.chat_ui import (
    message_display,
    message_display_with_link,
    reset_chat_history,
)
from src.utils.chatutils import get_response, get_final_response
from src.utils.sqlutils import get_result
from src.utils.bigqueryutils import get_database
from src.utils.chartutils import generate_chart, format_string

# from src.utils.snowflakeutils import get_database
from src.utils.llmutils import convert_to_langchainmsg
from datetime import datetime
from langchain.memory import ConversationBufferMemory
import uuid

memory = ConversationBufferMemory(
    return_messages=True, output_key="answer", input_key="input"
)

### Initialize state variables
state_vars = ["table_id", "session_id", "previous_query"]
for i in state_vars:
    if i not in st.session_state:
        st.session_state[i] = None

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

if "db" not in st.session_state:
    db = get_database()
    st.session_state.db = db

if "query" not in st.session_state:
    st.session_state.query = ""

### Set the configuration of the page
st.set_page_config(
    page_title="Marketing Analaytics Bot",
    page_icon=":robot_face:",
    layout="centered",
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    
    /* Apply Montserrat to the entire app */
    body, .stApp, .stTextInput, .stTextInput > div > div > input, .stPlaceholder, .stButton > button, .stSidebar, .stSidebar .sidebar-content {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Ensure Streamlit elements use Montserrat */
    .element-container, .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Style for message bubbles */
    .message-bubble {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Style for the placeholder text */
    .stTextInput > div > div > input::placeholder {
        font-family: 'Montserrat', sans-serif !important;
        color: #888;
    }
    
    /* Style for all buttons, including sidebar buttons */
    .stButton > button, .stSidebar .stButton > button {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500;
        font-size: 0.8rem;
        border-radius: 7px;
        border: none;
        padding: 8px 16px;
        transition: all 0.3s ease;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
        margin: 0 10px;
        background-color: #000080;  /* Navy blue */
        color: white;  /* White text */
    }
    
    /* Button hover effect for all buttons */
    .stButton > button:hover, .stSidebar .stButton > button:hover {
        background-color: #000066;  /* Slightly darker navy blue on hover */
        color: white;
    }
    
    /* Apply styles to sidebar */
    .stSidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    
    .stSidebar .sidebar-content * {
        font-family: 'Montserrat', sans-serif !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Explicitly load the Montserrat font
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

st.title("Marketing Analytics Bot")

messages_container = st.container()

if "generated" not in st.session_state:
    st.session_state["generated"] = (
        "Hey there, I'm the Marketing Analytics  Bot, ready to chat up on any questions you might have regarding the data in the database."
    )


if "past" not in st.session_state:
    st.session_state["past"] = "Hey!"
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        (
            "Hello! I'm Marketing Analytics chatbot designed to help you with questions related to the properties in our portfolio."
        )
    ]


### ----------------- Functionalities on the sidebar --------------------------------

with st.sidebar:

    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    ## ------------------ Add logo ----------------------------------------------------

    import base64

    with open("images/logo.PNG", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

        st.sidebar.markdown(
            f"""
            <div style="display:table;margin-top:-20%;margin-left:6%;">
                <img src="data:image/png;base64,{data}" width="250" height="100">
            </div><br>
            """,
            unsafe_allow_html=True,
        )
        st.sidebar.markdown("")

    col1, col2, col3, col4 = st.columns([1, 4.5, 3.5, 1.1])
    st.write("")
    st.write("")
    st.write("")

    ### ------------------------- New Chat functionality---------------------------------

    with col2:
        new_chat_button = st.button(
            label="New Chat",
            help="Click to start a new chat!",
            use_container_width=True,
        )

        if new_chat_button:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.chat_history = []
            st.session_state.conversation = []
            reset_chat_history()

        ### ------------------------- Logout functionality -----------------------------------

    with col3:
        logoutbutton = st.button(
            label="Logout", help="Click to log out!", use_container_width=True
        )
        if logoutbutton:
            st.session_state
            st.session_state.end_time = str(datetime.now())
            st.switch_page("app.py")

### -------------- Defining the chat box and submit, reset buttons -------------


def submit():
    st.session_state.query = st.session_state.widget
    st.session_state.widget = ""


c1, c2, c3, c4 = st.columns([6.2, 1, 0.01, 1])
with c1:
    st.text_input(
        label="Query",
        # key="input",
        key="widget",
        value="",
        placeholder="Ask your question here...",
        label_visibility="collapsed",
        on_change=submit,
    )
    # st.session_state.query = query

with c2:
    submit_button = st.button("Submit")

with c4:
    reset_button = st.button("Reset")


### ------------ Reset button ---------------------

if reset_button:
    st.session_state.session_id = str(uuid.uuid4())
    del st.session_state["db"]
    st.session_state.chat_history = []
    st.session_state.conversation = []
    reset_chat_history()


### ------------------------ Chat functionality ---------------------------------

if (
    (len(st.session_state.query) > 1)
    and (st.session_state.query != st.session_state.previous_query)
) or submit_button:

    messages = st.session_state["messages"]

    result, sql_query = get_final_response(
        user_query=st.session_state.query,
        chat_history=convert_to_langchainmsg(st.session_state.chat_history)[-10:],
        # db=st.session_state.db,
    )

    st.session_state.chat_history.append(st.session_state.query)
    st.session_state.chat_history.append(result["nlp_output"])
    st.session_state.conversation.append(st.session_state.query)
    st.session_state.conversation.append(result)
    st.session_state.previous_query = st.session_state.query


### -------------------- This displays the chat window ------------------------

with messages_container:
    message_display(st.session_state["past"], is_user=True)
    message_display(st.session_state["generated"])
    if st.session_state.chat_history != []:
        for i in range(len(st.session_state.conversation)):
            if i % 2 == 0:
                message_display(st.session_state["conversation"][i], is_user=True)
            else:
                message_display(st.session_state["conversation"][i]["nlp_output"])
                if st.session_state["conversation"][i]["sql_response"] != "N/A":
                    sql_response_dict = st.session_state["conversation"][i][
                        "sql_response"
                    ]
                    plot_columns = st.session_state["conversation"][i]["plot_columns"]
                    df = pd.DataFrame(sql_response_dict)
                    intent_type = st.session_state["conversation"][i]["intent_type"]
                    if intent_type != "forecasting":
                        df.fillna(0, inplace=True)
                        # Rounding the values to nearest
                        for col in df.select_dtypes(include=["float"]):
                            max_value = df[col].max()
                            min_value = df[col].min()
                            if max_value - min_value > 100:
                                df[col] = df[col].round(0)
                                df[col] = df[col].astype("int64")
                            else:
                                df[col] = df[col].round(2)
                    generate_chart(df, intent_type, plot_columns)

hide_footer = """
                <style>
                footer {visibility: hidden;}
                </style>
            """
st.markdown(hide_footer, unsafe_allow_html=True)
