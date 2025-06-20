import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from agents.exception_agent import agent
from tools.shipment_tools import get_exception_details, get_conversation_history
from tools.llm_utils import get_llm_response

# --- UI ENHANCEMENTS ---
# Show company logo at the top
st.image("static/logo.png", width=120)
st.markdown("<h1 style='display:inline; vertical-align:middle;'>📦 Bot Gurus Query Resolution Chatbot</h1>", unsafe_allow_html=True)

# Quick action buttons for FAQ and support
col1, col2 = st.columns(2)
with col1:
    if st.button("❓ FAQ"):
        st.markdown("[Visit our FAQ](https://chatgpt.com/g/g-6847c1b032788191ba69212538ccf3f0-engage360-support-gpt)")
with col2:
    if st.button("📧 Contact Support"):
        st.markdown("Email us at [support@shiprocket.com](mailto:support@shiprocket.com)")

# --- END UI ENHANCEMENTS ---

# Check for OpenAI API key and warn if missing
if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY is missing! Please add it to your .env file.")

st.set_page_config(page_title="Bot Gurus Chatbot", page_icon="📦")

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! 👋 Please describe your shipment issue."}
    ]
if "awaiting_shipment_id" not in st.session_state:
    st.session_state.awaiting_shipment_id = False
if "issue_description" not in st.session_state:
    st.session_state.issue_description = ""
if "shipment_id" not in st.session_state:
    st.session_state.shipment_id = ""

# Display chat history with avatar and markdown
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").markdown(f"<img src='static/avtar.jpeg' width='32' style='vertical-align:middle; border-radius:50%; margin-right:8px;'/>  {msg['content']}", unsafe_allow_html=True)

# User input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not st.session_state.awaiting_shipment_id:
        # First, get the issue description
        st.session_state.issue_description = prompt
        st.session_state.awaiting_shipment_id = True
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Thank you! 🙏 Please provide your shipment ID (or describe your shipment issue)."
        })
    else:
        # Now, get the shipment ID and resolve the issue
        st.session_state.shipment_id = prompt
        st.session_state.awaiting_shipment_id = False

        # --- Spinner while waiting for LLM response ---
        with st.spinner('🔄 Checking shipment status and searching for solutions...'):
            exception_type, details = get_exception_details(st.session_state.shipment_id)
            conversation_history = get_conversation_history(st.session_state.shipment_id)

            # Placeholder for future data sources (e.g., Shiprocket, Engage360 APIs)
            # def get_additional_shipment_info(shipment_id):
            #     # Example: Call external APIs or load more CSVs here
            #     return None
            # additional_info = get_additional_shipment_info(st.session_state.shipment_id)

            # Handle invalid shipment ID or not found
            if details == "Invalid shipment ID. Please enter a numeric shipment ID.":
                # Use a more conversational, company-specific prompt
                prompt_llm = (
                    f"A user has entered the following as a shipment identifier or query: '{st.session_state.shipment_id}'. "
                    f"This is not a numeric shipment ID. You are a helpful support agent for Bot Gurus, a company specializing in automated shipment exception resolution. "
                    f"Please try to help the user with their shipment-related question or issue, searching external sources (such as Shiprocket, Engage360, or general knowledge) if needed. "
                    f"If you cannot find a shipment, provide empathetic guidance and suggest what the user should do next (e.g., contact support at support@botgurus.com, check with their shipping provider, or visit our FAQ at https://botgurus.com/faq). "
                    f"Always be friendly, clear, and actionable in your response."
                )
                resolution = get_llm_response(prompt_llm)
                st.session_state.messages.append({"role": "assistant", "content": f"🤖 **Bot Gurus Assistant:**\n\n{resolution}"})
                st.session_state.awaiting_shipment_id = True
            elif exception_type:
                detected_issue = f"**Shipment {st.session_state.shipment_id}** has an exception: **{exception_type}** — {details}."
                st.session_state.messages.append({"role": "assistant", "content": f"🚨 {detected_issue}"})
                # Build a rich prompt for the LLM
                context = f"Exception type: {exception_type}\nException details: {details}\n"
                if conversation_history:
                    conv_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history])
                    st.session_state.messages.append({"role": "assistant", "content": f"🗣️ **Conversation history:**\n{conv_str}"})
                    context += f"Conversation history:\n{conv_str}\n"
                context += f"User issue description: {st.session_state.issue_description}\n"
                prompt_llm = (
                    f"You are a shipment support assistant for Bot Gurus, a company specializing in automated shipment exception resolution. "
                    f"Given the following context, your job is to:\n"
                    f"1. Identify the exact exception and its details for the shipment.\n"
                    f"2. Use the conversation history to understand what has already been tried or discussed.\n"
                    f"3. Provide a clear, step-by-step, and friendly resolution for the user that addresses the exception directly, using all available information.\n"
                    f"4. Never suggest escalation to a human agent. Always provide a concrete, actionable resolution, even if you have to make reasonable assumptions.\n\n"
                    f"{context}\n"
                    f"Your response should:\n"
                    f"- Clearly state the identified exception and details.\n"
                    f"- Reference any relevant points from the conversation history.\n"
                    f"- Give specific, actionable steps for the user to resolve the issue.\n"
                    f"- If the user needs more help, suggest contacting support at support@botgurus.com or visiting https://botgurus.com/faq.\n"
                )
                resolution = get_llm_response(prompt_llm)
                st.session_state.messages.append({"role": "assistant", "content": f"✅ **Recommended resolution:**\n\n{resolution}"})
            else:
                # Numeric but not found in CSV: ask LLM to act as a human searching external sources
                prompt_llm = (
                    f"A user has asked about shipment ID {st.session_state.shipment_id}, which is not found in our shipment_logs.csv database. "
                    f"You are a helpful support agent for Bot Gurus, a company specializing in automated shipment exception resolution. "
                    f"Search external sources (such as Shiprocket, Engage360, or general knowledge) and provide helpful next steps or guidance for the user. "
                    f"If you cannot find the shipment, provide empathetic guidance and suggest what the user should do next (e.g., contact support at support@botgurus.com, check with their shipping provider, or visit our FAQ at https://botgurus.com/faq). "
                    f"Always be friendly, clear, and actionable in your response."
                )
                resolution = get_llm_response(prompt_llm)
                st.session_state.messages.append({"role": "assistant", "content": f"🔍 **Shipment ID not found in our records.**\n\n{resolution}"})
                st.session_state.awaiting_shipment_id = True

    st.rerun() 