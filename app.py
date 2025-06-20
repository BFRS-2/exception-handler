import os
from dotenv import load_dotenv
load_dotenv()
print("OPENAI_API_KEY loaded:", os.getenv("OPENAI_API_KEY"))

import streamlit as st
import pandas as pd
from agents.exception_agent import agent
from tools.shipment_tools import get_exception_details, get_conversation_history
from tools.llm_utils import get_llm_response
from vectorstore.chroma_db import get_top_similar_conversations, load_corrections_to_chroma, get_top_similar_corrections

# Load corrections into ChromaDB at startup
load_corrections_to_chroma("data/corrections.csv")

st.set_page_config(page_title="Shipment Exception Chatbot", page_icon="📦")
st.title("📦 Shipment Exception Resolution Chatbot")

tab1, tab2 = st.tabs(["User Chatbot", "Admin Feedback Review"])

with tab1:
    # Check for OpenAI API key and warn if missing
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is missing! Please add it to your .env file.")

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
    if "last_resolution" not in st.session_state:
        st.session_state.last_resolution = None
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None

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
                # Retrieve top 2 similar corrections from ChromaDB
                similar_corrections = get_top_similar_corrections(st.session_state.issue_description, k=2, min_score=0.75)
                if similar_corrections:
                    corrections_str = "\n\n".join([f"Admin-verified Case {i+1}:\n{case.page_content}" for i, case in enumerate(similar_corrections)])
                    context += f"Admin-verified resolutions:\n{corrections_str}\n"
                # Retrieve top 3 similar conversations from ChromaDB
                similar_cases = get_top_similar_conversations(st.session_state.issue_description, k=3, min_score=0.75)
                if similar_cases:
                    similar_str = "\n\n".join([f"Similar Case {i+1}:\n{case.page_content}" for i, case in enumerate(similar_cases)])
                    context += f"Similar past cases:\n{similar_str}\n"
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
                # Store last prompt and resolution for feedback
                st.session_state.last_resolution = resolution
                st.session_state.last_prompt = prompt_llm
            else:
                st.session_state.messages.append({"role": "assistant", "content": "No exception found for this shipment ID. Please provide a valid shipment ID."})
                st.session_state.awaiting_shipment_id = True

        st.rerun()

    # Feedback UI after LLM response
    if st.session_state.last_resolution:
        st.write("#### Was this resolution helpful?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Yes", key="feedback_yes"):
                os.makedirs("data", exist_ok=True)
                feedback_path = "data/feedback.csv"
                if not os.path.exists(feedback_path):
                    with open(feedback_path, "w") as f:
                        f.write("issue_description,shipment_id,prompt,response,feedback\n")
                with open(feedback_path, "a") as f:
                    f.write(f'"{st.session_state.issue_description}","{st.session_state.shipment_id}","{st.session_state.last_prompt}","{st.session_state.last_resolution}","yes"\n')
                st.success("Thank you for your feedback! Have a great day.")
                st.session_state.last_resolution = None
                st.rerun()
        with col2:
            feedback_text = st.text_input("What was wrong or how can we improve?", key="feedback_text")
            if st.button("Submit Feedback", key="submit_feedback"):
                os.makedirs("data", exist_ok=True)
                feedback_path = "data/feedback.csv"
                if not os.path.exists(feedback_path):
                    with open(feedback_path, "w") as f:
                        f.write("issue_description,shipment_id,prompt,response,feedback\n")
                with open(feedback_path, "a") as f:
                    f.write(f'"{st.session_state.issue_description}","{st.session_state.shipment_id}","{st.session_state.last_prompt}","{st.session_state.last_resolution}","no: {feedback_text}"\n')
                st.error("Our tech support specialist will connect with you to help resolve this soon.")
                st.session_state.last_resolution = None
                st.rerun()

with tab2:
    st.header("Admin Feedback Review")
    feedback_path = "data/feedback.csv"
    if not os.path.exists(feedback_path):
        st.info("No feedback has been collected yet.")
    else:
        df = pd.read_csv(feedback_path)
        df["feedback"] = df["feedback"].fillna("").astype(str)
        # Filter for negative feedback
        negative_feedback = df[df["feedback"].str.startswith("no:")]
        if negative_feedback.empty:
            st.success("No negative feedback found! 🎉")
        else:
            for idx, row in negative_feedback.iterrows():
                st.markdown(f"**Issue:** {row['issue_description']}")
                st.markdown(f"**Shipment ID:** {row['shipment_id']}")
                st.markdown(f"**Prompt:** `{row['prompt']}`")
                st.markdown(f"**LLM Response:** {row['response']}")
                st.markdown(f"**User Feedback:** {row['feedback']}")
                # Optional: Allow admin to enter a correct resolution
                corrected = st.text_area(f"Corrected Resolution for Shipment {row['shipment_id']} (optional)", key=f"correct_{idx}")
                if st.button(f"Save Correction {idx}"):
                    # Save the correction to a new file for retraining or review
                    with open("data/corrections.csv", "a") as f:
                        f.write(f'"{row["issue_description"]}","{row["shipment_id"]}","{row["prompt"]}","{row["response"]}","{row["feedback"]}","{corrected}"\n')
                    st.success("Correction saved!")

                st.markdown("---") 