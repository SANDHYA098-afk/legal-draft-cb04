import streamlit as st
import requests
import os

# -------------------------------
# Configuration
# -------------------------------
st.set_page_config(page_title="Legal Chat Assistant")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# -------------------------------
# Session State Initialization
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "stage" not in st.session_state:
    st.session_state.stage = "intro"

if "doc_type" not in st.session_state:
    st.session_state.doc_type = ""

if "party_a_details" not in st.session_state:
    st.session_state.party_a_details = ""

if "party_b_details" not in st.session_state:
    st.session_state.party_b_details = ""

if "final_draft" not in st.session_state:
    st.session_state.final_draft = ""

# -------------------------------
# Document Type Options
# -------------------------------
DOCUMENT_OPTIONS = {
    "1": "lease agreement",
    "2": "nda",
    "3": "contract",
    "4": "employment agreement",
    "5": "educational agreement",
    "6": "freelance agreement"
}

# -------------------------------
# Helper Functions
# -------------------------------
def detect_document_type(user_input):
    user_input = user_input.lower()
    for key, val in DOCUMENT_OPTIONS.items():
        if key in user_input or val in user_input:
            return val
    return None

def generate_document_template(doc_type, party_a, party_b):
    return f"""
*{doc_type.upper()}*

This {doc_type} is made between the following parties:

*Party A:*  
{party_a}

*Party B:*  
{party_b}

This {doc_type} outlines the terms and agreements mutually accepted by both parties. It shall remain in effect until terminated under the governing law.

*Signatures:*  
____________________       ____________________  
Party A                         Party B
"""

def query_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://your-app.com",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mixtral-8x7b",
        "messages": [{"role": "user", "content": prompt}]
    }
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    else:
        return "⚠ Failed to fetch response from OpenRouter."

# -------------------------------
# Main App Interface
# -------------------------------
st.title("🧑‍⚖ Legal Agentic Chat Assistant")
tab1, tab2 = st.tabs(["📄 Document Drafting", "🔎 Legal Clarification"])

# -------------------------------
# Module 1: Document Drafting
# -------------------------------
with tab1:
    user_input = st.chat_input("You:")

    if user_input:
        st.session_state.chat_history.append(("user", user_input.lower()))

        if st.session_state.stage == "intro":
            st.session_state.chat_history.append((
                "bot",
                "*Hello!* How can I assist you today?\n\nPlease select a document type:\n\n1. Lease Agreement\n2. NDA\n3. Contract\n4. Employment Agreement\n5. Educational Agreement\n6. Freelance Agreement\n\n(Reply with number or name)"
            ))
            st.session_state.stage = "await_doc_type"

        elif st.session_state.stage == "await_doc_type":
            detected_type = detect_document_type(user_input)
            if detected_type:
                st.session_state.doc_type = detected_type
                st.session_state.stage = "ask_party_a"
                st.session_state.chat_history.append((
                    "bot",
                    f"Great! You've selected *{detected_type.title()}.\n\nPlease provide the details of **Party A*:\n\nParty A Name:\nResidential address:\nContact number:\nType of occupation:\nCity:\nState:"
                ))
            else:
                st.session_state.chat_history.append((
                    "bot",
                    "I couldn’t detect a valid document type. Please reply with a valid number (1–6) or name from the list."
                ))

        elif st.session_state.stage == "ask_party_a":
            st.session_state.party_a_details = user_input
            st.session_state.stage = "ask_party_b"
            st.session_state.chat_history.append(("bot", "Now, please provide the details of *Party B* in the same format:\n\nParty B Name:\nResidential address:\nContact number:\nType of occupation:\nCity:\nState:"))

        elif st.session_state.stage == "ask_party_b":
            st.session_state.party_b_details = user_input
            st.session_state.stage = "show_draft"
            st.session_state.chat_history.append(("bot", "Thank you! Preparing your legal document..."))

            final_doc = generate_document_template(
                st.session_state.doc_type,
                st.session_state.party_a_details,
                st.session_state.party_b_details
            )
            st.session_state.final_draft = final_doc
            st.session_state.chat_history.append(("bot", final_doc))

        for sender, msg in st.session_state.chat_history:
            if sender == "user":
                st.chat_message("user").markdown(msg)
            else:
                st.chat_message("assistant").markdown(msg)

        if st.session_state.final_draft:
            st.download_button(
                label="📥 Download Document",
                data=st.session_state.final_draft,
                file_name=f"{st.session_state.doc_type.replace(' ', '_')}_draft.txt",
                mime="text/plain"
            )

# -------------------------------
# Module 2: Legal Clarification
# -------------------------------
with tab2:
    st.subheader("Ask a legal question:")
    question = st.text_input("e.g., What's the difference between void and voidable contracts?")
    if st.button("Ask"):
        if question.strip():
            response = query_openrouter(question)
            st.markdown(f"*Answer:*\n\n{response}")
