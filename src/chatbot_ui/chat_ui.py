import streamlit as st
import base64


def message_display(text, is_user=False):

    text_html = text.replace("\n", "<br>")
    if is_user:
        with open("images/user.png", "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        message_alignment = "flex-end"
        message_bg_color = "#F0F2F6"
        avatar_class = "user-avatar"
        #   st.write(
        #       f"""
        #   <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
        #     <div style="background: {message_bg_color}; color: black; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%;">
        #       {text_html}
        #     </div>
        #     <img src="data:image/png;base64,{data}" class="{avatar_class}" alt="user" width="50" height="50" />

        #   </div>
        # """,
        #       unsafe_allow_html=True,
        #   )
        st.write(
            f"""
      <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
        <div class="message-bubble" style="background: {message_bg_color}; color: black; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%;">
          {text_html}
        </div>
        <img src="data:image/png;base64,{data}" class="{avatar_class}" alt="user" width="50" height="50" />
      </div>
      """,
            unsafe_allow_html=True,
        )

    else:
        with open("images/robot.png", "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        message_alignment = "flex-start"
        message_bg_color = "#F0F2F6"
        avatar_class = "bot-avatar"
        #   st.write(
        #       f"""
        #   <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
        #     <img src="data:image/png;base64,{data}" class="{avatar_class}" alt="robot" width="50" height="50" />
        #     <div style="background: {message_bg_color}; color: black; border-radius: 20px; padding: 10px; margin-left: 5px; margin-bottom: 30px; max-width: 75%;">
        #       {text_html} \n
        #     </div>
        #   </div>
        # """,
        #       unsafe_allow_html=True,
        #   )

        st.write(
            f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
        <img src="data:image/png;base64,{data}" class="{avatar_class}" alt="robot" width="50" height="50" />
              <div class="message-bubble" style="background: {message_bg_color}; color: black; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%;">
                {text_html}
              </div>              
            </div>
            """,
            unsafe_allow_html=True,
        )


def message_display_with_link(response, is_user=False):
    text = response["nlp_output"]
    text_html = text.replace("\n", "<br>")
    text_html += f"""<br><br>You can visit the below link to know more about the property:<a href="{response['property_link']}">{response['property_link']}</a>"""
    with open("images/robot.png", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    message_alignment = "flex-start"
    message_bg_color = "#F0F2F6"
    avatar_class = "bot-avatar"
    st.write(
        f"""
    <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
      <img src="data:image/png;base64,{data}" class="{avatar_class}" alt="robot" width="50" height="50" />
      <div class="message-bubble" style="background: {message_bg_color}; color: black; border-radius: 20px; padding: 10px; margin-left: 5px; margin-bottom: 30px; max-width: 75%;">
        {text_html}
      </div>
    </div>
  """,
        unsafe_allow_html=True,
    )
    # st.write(
    #     f"""
    #     <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
    #       <div class="message-bubble" style="background: {message_bg_color}; color: black; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%;">
    #         {text_html}
    #       </div>
    #       <img src="data:image/png;base64,{data}" class="{avatar_class}" alt="user" width="50" height="50" />
    #     </div>
    #     """,
    #     unsafe_allow_html=True,
    # )


def reset_chat_history():
    st.session_state["generated"] = (
        "Hey there, I'm SQL Bot, ready to chat up on any questions you might have regarding the data in your database."
    )
    st.session_state["past"] = "Hi..."
    st.session_state["conversation"] = []
    st.session_state["chat_history"] = []
    st.session_state["messages"] = [
        ("Hello! I'm a chatbot designed to help you with data in your database.")
    ]
