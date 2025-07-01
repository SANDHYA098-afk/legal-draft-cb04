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
        return "âš ï¸ Failed to fetch response from OpenRouter."

# -------------------------------
# Main App Interface
# -------------------------------
st.title("ðŸ§‘â€âš–ï¸ Legal Agentic Chat Assistant")
tab1, tab2 = st.tabs(["ðŸ“„ Document Drafting", "ðŸ”Ž Legal Clarification"])

# -------------------------------
# Module 1: Document Drafting
# -------------------------------
with tab1:
    # Show the chat history in order
    for sender, msg in st.session_state.chat_history:
        if sender == "user":
            st.chat_message("user").markdown(msg)
        else:
            st.chat_message("assistant").markdown(msg)

    # User Input (chat-style)
    user_input = st.chat_input("Type your message here...")

    if user_input:
        user_input_lower = user_input.lower()
        st.session_state.chat_history.append(("user", user_input))

        if st.session_state.stage == "intro":
            bot_message = """*Hello!* How can I assist you today?

Please select a document type:
1. Lease Agreement  
2. NDA  
3. Contract  
4. Employment Agreement  
5. Educational Agreement  
6. Freelance Agreement  

(Reply with number or name)"""
            st.session_state.chat_history.append(("assistant", bot_message))
            st.session_state.stage = "await_doc_type"

        elif st.session_state.stage == "await_doc_type":
            detected_type = detect_document_type(user_input_lower)
            if detected_type:
                st.session_state.doc_type = detected_type
                st.session_state.stage = "ask_party_a"
                bot_message = f"""You've selected *{detected_type.title()}*.

Please provide the details of *Party A* in the following format:


Party A Name:  
Residential address:  
Contact number:  
Type of occupation:  
City:  
State:
"""
                st.session_state.chat_history.append(("assistant", bot_message))
            else:
                st.session_state.chat_history.append((
                    "assistant",
                    "âš ï¸ I couldnâ€™t detect a valid document type. Please reply with a valid number (1â€“6) or name from the list."
                ))

        elif st.session_state.stage == "ask_party_a":
            st.session_state.party_a_details = user_input
            st.session_state.stage = "ask_party_b"
            bot_message = """Now, please provide the details of *Party B* in the same format:


Party B Name:  
Residential address:  
Contact number:  
Type of occupation:  
City:  
State:
"""
            st.session_state.chat_history.append(("assistant", bot_message))

        elif st.session_state.stage == "ask_party_b":
            st.session_state.party_b_details = user_input
            st.session_state.stage = "show_draft"
            st.session_state.chat_history.append(("assistant", "âœ… Thank you! Preparing your legal document..."))

            # Final document creation
            final_doc = generate_document_template(
                st.session_state.doc_type,
                st.session_state.party_a_details,
                st.session_state.party_b_details
            )
            st.session_state.final_draft = final_doc
            st.session_state.chat_history.append(("assistant", f"Here is your *{st.session_state.doc_type.title()}*:

" + final_doc))

    # After document is generated, show download button
    if st.session_state.final_draft:
        st.download_button(
            label="ðŸ“¥ Download Document",
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
            st.markdown(f"*Answer:*

{response}")
