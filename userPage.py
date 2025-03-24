import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from fileprocessing import process_document
from vectordb import add_to_collection
from chatFunctions import save_chat_sessions, load_chat_sessions, new_chat_id
from streamlitfunctions import query_and_display_response, handle_chat_button
from uservalidate import get_user_cost
from datetime import datetime
from styles import (
    get_main_styles,
    get_sidebar_button_styles,
    get_main_container_styles,
    get_button_styles,
    get_bottom_container_styles,
    get_bottom_content_styles,
    get_user_dropdown_styles,
    get_main_section_styles
)

# Get the API Key
api_key = st.secrets["api_keys"]["openai"]

def user_page(username):
    """User chat interface page"""

    # Apply styles
    st.markdown(get_main_styles(), unsafe_allow_html=True)
    st.markdown(get_sidebar_button_styles(), unsafe_allow_html=True)

    # Set page variables
    total_cost = get_user_cost(username)
    month = datetime.now().strftime("%B")
    
    # Show user dropdown
    st.markdown(
        get_user_dropdown_styles(username, month, total_cost),
        unsafe_allow_html=True
    )

    # Initialize chat sessions
    if "chat_sessions" not in st.session_state:
        # Initialize chat_sessions if not already set
        st.session_state.chat_sessions = load_chat_sessions(username)

    # Add favorite field to existing chats if it doesn't exist
    for chat in st.session_state.chat_sessions:
        if "favorite" not in chat:
            chat["favorite"] = False

    # Create a new chat if none exist
    if not st.session_state.chat_sessions:
        st.session_state.current_chat_id = new_chat_id()
        save_chat_sessions(st.session_state.chat_sessions, username)
        
    # Set current chat if not set
    elif "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = st.session_state.chat_sessions[0]["chat_id"]

    # Sidebar for chat history
    with st.sidebar:

        st.header("Chat History")
        col1, col2, col3 = st.columns([6, 1, 6])
        
        with col1:
            # Add New Chat button at the top
            if st.button("➕ New Chat", key="new_chat_button"):
                new_id = new_chat_id()
                st.session_state.current_chat_id = new_id
                save_chat_sessions(st.session_state.chat_sessions, username)
                st.rerun()
        
        with col3:
            temperature = st.slider("Creativity", min_value=0.0, max_value=1.0, value=st.session_state.temperature, step=0.1)
            st.session_state.temperature = temperature
        
        # Organize Favorites and Old Chats
        favorites = [chat for chat in st.session_state.chat_sessions if chat.get("favorite", False)]
        old_chats = [chat for chat in st.session_state.chat_sessions if not chat.get("favorite", False)]
        favorites = sorted(favorites, key = lambda x: -st.session_state.chat_sessions.index(x))
        old_chats = sorted(old_chats, key = lambda x: -st.session_state.chat_sessions.index(x))

        if favorites:
            st.subheader("Favorites")
            for chat in favorites:
                is_active = st.session_state.current_chat_id == chat["chat_id"]
                handle_chat_button(chat, is_active, "★", False)

        if old_chats:
            st.subheader("Old Chats")
            for chat in old_chats:
                is_active = st.session_state.current_chat_id == chat["chat_id"]
                handle_chat_button(chat, is_active, "☆", True)

    # Main chat area

    st.markdown(get_main_section_styles(), unsafe_allow_html=True)

    st.markdown("<div><h1 style='text-align: center;'>SCA AI Pilot</h1></div>", unsafe_allow_html=True)
    
    # Apply main container styles
    st.markdown(get_main_container_styles(), unsafe_allow_html=True)
    
    chat_container = st.container(key="mainContainer")
    
    with chat_container:
        current_chat = next((chat for chat in st.session_state.chat_sessions
        if chat["chat_id"] == st.session_state.current_chat_id), None)

        if current_chat:
            for message in current_chat["messages"]:
                st.chat_message("user").markdown(message["question"])
                st.chat_message("assistant").markdown(message["answer"], unsafe_allow_html=True)
        else:
            st.write("")

    if "thinking" not in st.session_state:
        st.session_state.thinking = False
    if "search" not in st.session_state:
        st.session_state.search = False
    if "image" not in st.session_state:
        st.session_state.image = False

    # Apply button styles
    st.markdown(get_button_styles(), unsafe_allow_html=True)
    
    # Place the custom buttons in your layout
    with stylable_container(
        key="bottomContent", 
        css_styles=get_bottom_container_styles()):
        
        prompt = st.chat_input("How may I help you?", 
                               accept_file=True, file_type=["pdf", "docx", "text", "csv", "xls", "xlsx", "xlsm"], 
                               disabled=False)

        col1, col2, col3, col4 = st.columns([2, 2, 2, 9])

        # Use different button colors based on state
        thinking_type = "primary" if st.session_state.thinking else "secondary"
        search_type = "primary" if st.session_state.search else "secondary"
        image_type = "primary" if st.session_state.image else "secondary"
        
        if col1.button("💡 Reason", key="toggle_thinking", type=thinking_type):
            st.session_state.thinking = not st.session_state.thinking
            st.rerun()
            
        if col2.button("🔍 Search", key="toggle_search", type=search_type):
            st.session_state.search = not st.session_state.search
            st.rerun()
        
        if col3.button("📷 Image", key="toggle_image", type=image_type):
            st.session_state.image = not st.session_state.image
            st.rerun()

    # Process file input first, if any
    if prompt and prompt.get("files") and prompt.get('text'):
        uploaded_file = prompt["files"][0]
        normalize_uploaded_file_name = uploaded_file.name.translate(
            str.maketrans({"-": "_", ".": "_", " ": "_"})
        )
        
        # Process the document and split it into chunks
        all_splits, file_size_bytes = process_document(uploaded_file)
        
        if all_splits and file_size_bytes > 0:
            # Setup user-specific vector store
            chat_id = st.session_state.current_chat_id
            store_path = f"rag_chroma_temp_{username}_{chat_id}"
            collection_name = f"sca_rag_temp_{username}_{chat_id}"
            
            # Add document chunks to vector store collection
            add_to_collection(all_splits, normalize_uploaded_file_name, file_size_bytes, api_key, store_path, collection_name)
            st.success(f"✅ File '{uploaded_file.name}' processed and added to knowledge base!")
        
        # Process the query with or without successful file upload
        query_and_display_response(prompt["text"], reasoning=st.session_state.thinking, search=st.session_state.search, images=st.session_state.image)
    
    # Handle regular text queries without file uploads
    elif prompt and prompt.get('text'):
        query_and_display_response(prompt["text"], reasoning=st.session_state.thinking, search=st.session_state.search, images=st.session_state.image)

    with stylable_container(
        key="bottom_content", 
        css_styles=get_bottom_content_styles()
    ):
        st.markdown('<span style="font-family: \'Segoe UI\', sans-serif; font-size: 0.8rem; font-style: italic;">This chatbot can make mistakes. Please verify important information.</span>', 
        unsafe_allow_html = True)
        
    return None 