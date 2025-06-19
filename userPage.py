import streamlit as st
import time
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.floating_button import floating_button
from fileprocessing import process_document
from vectordb import add_to_collection
from chatFunctions import save_chat_sessions, load_chat_sessions, new_chat_id
from streamlitfunctions import handle_chat_button, query_and_display_response
from chatFunctions import append_message_to_current_chat
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
    get_main_section_styles,
    get_latex_styles
)
from agents import (
    software_development,
    generic_agent_Setup,
    Nuclear_research,
    Energy_market_research
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
        
    # Initialize state variables if not set
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
    if "search" not in st.session_state:
        st.session_state.search = False
    if "image" not in st.session_state:
        st.session_state.image = False
    if "raw_history" not in st.session_state:
        st.session_state.raw_history = []
    if "mini_summaries" not in st.session_state:
        st.session_state.mini_summaries = []
    if "turn_counter" not in st.session_state:
        st.session_state.turn_counter = 0
    if "chat_responses" not in st.session_state:
        st.session_state.chat_response = []

    # Sidebar for chat history
    with st.sidebar:
        
        st.header("Agent Controls")
        col1, col2 = st.columns([2, 1])
        with col1:
            task_type = st.selectbox(label="Task Type", label_visibility="visible", index = 0,
                options=["Software Development", "Nuclear Research", "Energy Market Research", "Custom Agent"])

        with col2:
            agents_count = st.selectbox(label="Agents Count", options=[1, 2, 3, 4, 5], index = 2, 
                label_visibility="visible", disabled = True if task_type!='Custom Agent' else False)


        st.header("Chat History")

        if st.button("➕ New Chat", key="new_chat_button"):
            new_id = new_chat_id()
            st.session_state.current_chat_id = new_id
            save_chat_sessions(st.session_state.chat_sessions, username)
            st.rerun()
        
        
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
        # Apply main container styles
    st.markdown(get_main_container_styles(), unsafe_allow_html=True)

    # Apply button styles
    st.markdown(get_button_styles(), unsafe_allow_html=True) 
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

    # Place the custom buttons in your layout
    with stylable_container(
        key="bottomContent", 
        css_styles=get_bottom_container_styles()
        ):
        
        prompt = st.chat_input("How may I help you?", key="inputPrompt",
            accept_file=True, file_type=["pdf", "docx", "text", "csv", "xls", "xlsx", "xlsm"], 
            disabled=False)

        search_type = "primary" if st.session_state.search else "secondary"
        image_type = "primary" if st.session_state.image else "secondary"

        # Use different button colors based on state
        col1, col2, col3, col4, col5, col6, col7  = st.columns([2, 2, 3, 2, 2, 2, 2])
        with col1:
            # I want to have selectboxes for agent selection, model selection, temperature slider and max_tokens
            model = st.selectbox(label="Model", label_visibility="hidden", placeholder="Agent", index=0,
                         options=["Model", "gpt-4o", "o1", "o3-mini", "gpt-4o-mini", "gpt-4.5", "o1-pro", "o1-mini"])
        
        with col2:
            manager_agent = st.selectbox(label="Manager", label_visibility="hidden", placeholder="Manager", index=0,
                         options=["Manager", "Yes", "No"], disabled= True if task_type=="Software Development" else False)

        with col3:
            temperature = st.slider(label="Creativity", label_visibility="hidden", min_value=0.0, 
                                    max_value=1.0, value=st.session_state.temperature, step=0.1)
            st.session_state.temperature = temperature
        with col4:
            max_tokens = st.number_input(label="max_tokens", min_value=128, max_value=16384, placeholder="Max Tokens",
                                         label_visibility="hidden", value=1024, step=1)
        
        with col5:
            task_nature = st.selectbox(label="Task Nature", label_visibility="hidden", placeholder="Task Nature", 
                                       index=0, options=["Agent", "Chat"])
        
        with col6:
            if task_nature != "Agent":
                internet_search = st.button(
                    ":material_captive_portal: Search",
                    key="toggle_search",
                    type=search_type,
                    help="Enable web search for your queries"
                )
        
        with col7:
            if task_nature != "Agent":
                image_button = st.button(
                    ":material/camera: Image",
                    key="toggle_image",
                    type=image_type,
                    help="Generate an image based on your prompt"
                )

    # Process user input (with or without file)
    if task_nature == "Chat":
        if prompt:
            full_response = query_and_display_response(prompt['text'])
            # Need to code here for chat mode. It should not be any agen. Here all the LLM models will come to work.
    if task_nature == "Agent": 
        if prompt:
            # Display user message
            if isinstance(prompt, dict):
                user_prompt = prompt.get('text', '')
            else:
                user_prompt = str(prompt)  # Ensure user_prompt is a string
            st.chat_message("user").markdown(user_prompt)
            
            # Process file if uploaded
            if isinstance(prompt, dict) and prompt.get("files") and prompt.get('text'):
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
                    st.success(f"✅ File '{uploaded_file.name}' processed and added to temporary knowledge base!")
            
            # Apply LaTeX styles for proper rendering
            st.markdown(get_latex_styles(), unsafe_allow_html=True)
            
            # Process the prompt with selected agent
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.info("Starting analysis of your prompt...")
                prompt_text = prompt['text']
                
                # Use default model if placeholder is selected
                model_to_use = "gpt-4o-mini" if model == "Model" else model
                
                # Handle manager agent selection
                manager_value = "Yes" if manager_agent == "Manager" or manager_agent == "Yes" else "No"
                
                # Initialize the appropriate agent based on task type
                if task_type == "Custom Agent":
                    crew = generic_agent_Setup(
                        query=prompt_text,
                        model=model_to_use, 
                        temperature=temperature, 
                        max_tokens=max_tokens, 
                        manager=manager_value,
                        agents_count=agents_count)
                elif task_type == "Software Development":
                    crew = software_development(
                        query=prompt_text,
                        model=model_to_use, 
                        temperature=temperature, 
                        max_tokens=max_tokens)
                elif task_type == "Nuclear Research":
                    crew = Nuclear_research(
                        query=prompt_text,
                        model=model_to_use, 
                        temperature=temperature, 
                        max_tokens=max_tokens)
                elif task_type == "Energy Market Research":
                    crew = Energy_market_research(
                        query=prompt_text,
                        model=model_to_use, 
                        temperature=temperature, 
                        max_tokens=max_tokens)
                
                # Execute the agent crew
                try:
                    crew_output = crew.kickoff()
                    
                    # Convert CrewOutput to string to make it JSON serializable
                    if hasattr(crew_output, "raw"):
                        full_response = str(crew_output.raw)
                    else:
                        full_response = str(crew_output)
                except Exception as e:
                    full_response = f"Error executing agent: {str(e)}"
                    st.error(full_response)

                # Display the response
                message_placeholder.empty()
                st.markdown(full_response, unsafe_allow_html=True)
                
                # Save the conversation to chat history
                append_message_to_current_chat(user_prompt, full_response)
    with stylable_container(
        key="bottom_content", 
        css_styles=get_bottom_content_styles()
    ):
        st.markdown('<span style="font-family: \'Segoe UI\', sans-serif; font-size: 0.8rem; font-style: italic;">This chatbot can make mistakes. Please verify important information.</span>', 
        unsafe_allow_html = True)
    
    # Help at the bottom right corner of the page
    @st.dialog("Support", width="small")
    def help_dialog():
        messages_container = st.container(height=400, border=False)
        write_stream = """
            This section has the usage information for maximizing output from the AI chatbot.
        
        """
        def stream_data():
            for word in write_stream.split(" "):
                yield word + " "
                time.sleep(0.02)
        with messages_container:
            st.write_stream(stream_data)    
    
    if floating_button(":material/help_center: Help"):
        help_dialog()


    return None
