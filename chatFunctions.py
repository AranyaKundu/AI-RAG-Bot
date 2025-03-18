import os, re, json
import streamlit as st

# Add username sanitization function
def sanitize_username(username: str) -> str:
    """Sanitize username for safe filename use"""
    return re.sub(r'[^a-zA-Z0-9]', '_', username)

# Get chat history filename based on username
def get_chat_history_filename(username: str) -> str:
    sanitized = sanitize_username(username)
    return f"{sanitized}_chat_history.json"

# Save the chat sessions to the chat history file
def save_chat_sessions(sessions, username: str):
    filename = get_chat_history_filename(username)
    with open(filename, "w") as f:
        json.dump(sessions, f)

# Load the chat sessions from chat history file
def load_chat_sessions(username: str) -> list:
    filename = get_chat_history_filename(username)
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# Append a new message to the current chat session
def append_message_to_current_chat(question: str, answer: str):
    for chat in st.session_state.chat_sessions:
        if chat["chat_id"] == st.session_state.current_chat_id:
            if not chat['messages']:
                chat["title"] = chat_title(question)
            chat["messages"].append({"question": question, "answer": answer})
            break
    if "username" in st.session_state:
        save_chat_sessions(st.session_state.chat_sessions, st.session_state.username)
    else:
        st.error("User not logged in!")

# Define a chat title based on first prompt question
def chat_title(first_prompt, max_length=50):
    if len(first_prompt) <= max_length:
        return first_prompt.strip()
    truncated = first_prompt[:max_length]
    last_space_index = truncated.rfind(" ")
    if last_space_index == -1:
        return truncated.strip() + "..."
    return truncated[:last_space_index].strip() + "..."