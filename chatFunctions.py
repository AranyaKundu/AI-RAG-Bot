import os, re, json, shutil, uuid
import streamlit as st

# Add username sanitization function
def sanitize_username(username: str) -> str:
    """Sanitize username for safe filename use"""
    return re.sub(r'[^a-zA-Z0-9]', '_', username)

# Ensure chat history directory exists
def ensure_chat_history_dir():
    """Create the chat history directory if it doesn't exist"""
    chat_dir = "userchathistory"
    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)
    return chat_dir

# Get chat history filename based on username
def get_chat_history_filename(username: str) -> str:
    sanitized = sanitize_username(username)
    chat_dir = ensure_chat_history_dir()
    return os.path.join(chat_dir, f"{sanitized}_chat_history.json")

# Save the chat sessions to the chat history file
def save_chat_sessions(sessions, username: str):
    filename = get_chat_history_filename(username)
    ensure_chat_history_dir()  # Make sure directory exists
    with open(filename, "w") as f:
        try:
            json.dump(sessions, f, default=str)  # Use default=str to handle non-serializable objects
        except TypeError as e:
            print(f"Error saving chat sessions: {e}")

# Load the chat sessions from chat history file
def load_chat_sessions(username: str) -> list:
    filename = get_chat_history_filename(username)
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    # Check for files in old location for backward compatibility
    old_filename = f"{sanitize_username(username)}_chat_history.json"
    if os.path.exists(old_filename):
        with open(old_filename, "r") as f:
            try:
                data = json.load(f)
                # Save to new location for future use
                save_chat_sessions(data, username)
                return data
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
        return first_prompt.text.strip()
    truncated = first_prompt[:max_length]
    last_space_index = truncated.rfind(" ")
    if last_space_index == -1:
        return truncated.strip() + "..."
    return truncated[:last_space_index].strip() + "..."

def delete_chat(chat_id):
    username = st.session_state.get("username")
    if username != "admin":
        temp_store_path = f"rag_chroma_temp_user_{username}_{chat_id}"
        if os.path.exists(temp_store_path):
            shutil.rmtree(temp_store_path)
    st.session_state.chat_sessions = [
        c for c in st.session_state.chat_sessions if c["chat_id"] != chat_id
    ]
    if st.session_state.chat_sessions:
        st.session_state.current_chat_id = st.session_state.chat_sessions[0]["chat_id"]
    else:
        new_chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_sessions.append({
            "chat_id": new_chat_id,
            "title": "New Chat",
            "messages": [],
            "favorite": False
        })
    save_chat_sessions(st.session_state.chat_sessions, username)
    st.success("Chat deleted successfully!")
    st.rerun()

def new_chat_id():
    """
        Generates a new chat ID and adds it to the session state. Returns the new chat ID.
    """
    new_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_id
    st.session_state.chat_sessions.append({
        "chat_id": new_id,
        "title": "New Chat",
        "messages": [],
        "favorite": False
    })
    return new_id
