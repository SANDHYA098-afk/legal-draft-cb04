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
    st.session_state.party_a_details = {}

if "party_b_details" not in st.session_state:
    st.session_state.party_b_details = {}

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

def parse_party_details(user_input):
    lines = user_input.strip().split("\n")
    details = {}
    for line in lines:
        if '.' in line:
            key, value = line.split('.', 1)
            details[key.strip()] = value.strip()
    return details

def format_party_details(details):
    return "\n".join([f"{k}. {v}" for k, v in details.items()])

def generate_document_template(doc_type, party_a, party_b):
    return f"""
*{doc_type.upper()}*

This {doc_type} is made between the following parties:

*Party A:*  
{format_party_details(party_a)}

*Party B:*  
{format_party_details(party_b)}

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
    # First show the chat history, THEN ask for input (to make it like normal chat)
    for sender, msg in st.session_state.chat_history:
        if sender == "user":
            st.chat_message("user").markdown(msg)
        else:
            st.chat_message("assistant").markdown(msg)

    user_input = st.chat_input("Type your message here...")

    if user_input:
        st.session_state.chat_history.append(("user", user_input))

        if st.session_state.stage == "intro":
            st.session_state.chat_history.append((
                "assistant",
                "*Hello!* How can I assist you today?\n\nPlease select a document type:\n\n1. Lease Agreement\n2. NDA\n3. Contract\n4. Employment Agreement\n5. Educational Agreement\n6. Freelance Agreement\n\n(Reply with number or name)"
            ))
            st.session_state.stage = "await_doc_type"

        elif st.session_state.stage == "await_doc_type":
            detected_type = detect_document_type(user_input)
            if detected_type:
                st.session_state.doc_type = detected_type
                st.session_state.stage = "ask_party_a"
                st.session_state.chat_history.append((
                    "assistant",
                    f"Great! You've selected *{detected_type.title()}.\n\nNow, provide the details of **Party A* in the format below:\n\n"
                    "1. Party Name:\n"
                    "2. Residential Address:\n"
                    "3. Contact Number:\n"
                    "4. Occupation:\n"
                    "5. City:\n"
                    "6. State:"
                ))
            else:
                st.session_state.chat_history.append((
                    "assistant",
                    "❌ I couldn’t detect a valid document type. Please reply with a valid number (1–6) or name from the list."
                ))

        elif st.session_state.stage == "ask_party_a":
            st.session_state.party_a_details = parse_party_details(user_input)
            st.session_state.stage = "ask_party_b"
            st.session_state.chat_history.append((
                "assistant",
                "Now, provide the details of *Party B* in the same format:\n\n"
                "1. Party Name:\n"
                "2. Residential Address:\n"
                "3. Contact Number:\n"
                "4. Occupation:\n"
                "5. City:\n"
                "6. State:"
            ))

        elif st.session_state.stage == "ask_party_b":
            st.session_state.party_b_details = parse_party_details(user_input)
            st.session_state.stage = "show_draft"
            st.session_state.chat_history.append(("assistant", "✅ Thank you! Preparing your legal document..."))

            final_doc = generate_document_template(
                st.session_state.doc_type,
                st.session_state.party_a_details,
                st.session_state.party_b_details
            )
            st.session_state.final_draft = final_doc
            st.session_state.chat_history.append(("assistant", final_doc))

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
