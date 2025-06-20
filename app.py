import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from agents.exception_agent import agent
from tools.shipment_tools import get_exception_details, get_conversation_history
from tools.llm_utils import get_llm_response

# Check for OpenAI API key and warn if missing
if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY is missing! Please add it to your .env file.")

st.set_page_config(page_title="Bot Gurus Chatbot", page_icon="📦")

st.title("📦 Bot Gurus Query Resolution Chatbot")

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Please describe your shipment issue."}
    ]
if "awaiting_shipment_id" not in st.session_state:
    st.session_state.awaiting_shipment_id = False
if "issue_description" not in st.session_state:
    st.session_state.issue_description = ""
if "shipment_id" not in st.session_state:
    st.session_state.shipment_id = ""

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# User input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not st.session_state.awaiting_shipment_id:
        # First, get the issue description
        st.session_state.issue_description = prompt
        st.session_state.awaiting_shipment_id = True
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Thank you. Please provide your shipment ID."
        })
    else:
        # Now, get the shipment ID and resolve the issue
        st.session_state.shipment_id = prompt
        st.session_state.awaiting_shipment_id = False

        # Lookup exception details and conversation history
        exception_type, details = get_exception_details(st.session_state.shipment_id)
        conversation_history = get_conversation_history(st.session_state.shipment_id)

        if exception_type:
            detected_issue = f"Shipment {st.session_state.shipment_id} has an exception: {exception_type} — {details}."
            st.session_state.messages.append({"role": "assistant", "content": detected_issue})
            # Build a rich prompt for the LLM
            context = f"Exception type: {exception_type}\nException details: {details}\n"
            if conversation_history:
                conv_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history])
                st.session_state.messages.append({"role": "assistant", "content": f"Conversation history:\n{conv_str}"})
                context += f"Conversation history:\n{conv_str}\n"
            context += f"User issue description: {st.session_state.issue_description}\n"
            prompt_llm = (
                f"You are a shipment support assistant for a chatbot. "
                f"Given the following context, your job is to:\n"
                f"1. Identify the exact exception and its details for the shipment.\n"
                f"2. Use the conversation history to understand what has already been tried or discussed.\n"
                f"3. Provide a clear, step-by-step resolution for the user that addresses the exception directly, using all available information.\n"
                f"4. Never suggest escalation to a human agent. Always provide a concrete, actionable resolution, even if you have to make reasonable assumptions.\n\n"
                f"{context}\n"
                f"Your response should:\n"
                f"- Clearly state the identified exception and details.\n"
                f"- Reference any relevant points from the conversation history.\n"
                f"- Give specific, actionable steps for the user to resolve the issue.\n"
            )
            resolution = get_llm_response(prompt_llm)
            st.session_state.messages.append({"role": "assistant", "content": f"Recommended resolution: {resolution}"})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "No exception found for this shipment ID. Please provide a valid shipment ID."})
            st.session_state.awaiting_shipment_id = True

    st.rerun() 