import streamlit as st
import time
from app import answer_query

st.set_page_config(page_title="Insurance AI Auditor", page_icon="🏦", layout="centered")

st.title("🏦 AI-Driven Insurance Knowledge Assessment System")
st.markdown("Ask questions about your **LIC Policies** and **IRDAI Guidelines**.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is the basic sum assured for Jeevan Anand?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Searching millions of tokens..."):
            # Call the exact same logic from app.py! No changes made to backend.
            result = answer_query(prompt)
            
            answer = result["answer"]
            sources = result["sources"]

            # Construct the final display string
            if "I could not find this information" in answer:
                display_text = answer
            else:
                display_text = f"{answer}\n\n**📚 SOURCES:**\n"
                for s in sources:
                    display_text += f"\n- {s['source_document']} — Page {s['page_number']}"

            st.markdown(display_text)
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": display_text})
