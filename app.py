import time, uuid, shutil, os
from datetime import datetime
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from fileprocessing import process_document
from vectordb import get_vector_collection, add_to_collection, query_collection
from llms import call_llm, call_reasoning_llm, search_web
from uservalidate import create_users_table, verify_user, add_user, get_user_cost
from chatFunctions import save_chat_sessions, load_chat_sessions



# Get the API Key
api_key = os.getenv("API_KEY")


# App specific codes: Design & Additional Features
def query_and_display_response(prompt, reasoning=False, search=False):
    results = query_collection(prompt, api_key)
    documents = results.get("documents")
    context_list = documents[0] if documents and len(documents) > 0 else None

    spinner_placeholder = st.empty()
    spinner_message = "Inventing Recipe..." if reasoning else "Analyzing Recipe..."
    spinner_placeholder.info(spinner_message)

    if not context_list:
        spinner_placeholder.info("Shopping ingedients now...")
        context = search_web(prompt)
    else:
        context = context_list[0]
        error_keywords = ["insufficient information", "does not contain any information"]
        if any(keyword in context.lower() for keyword in error_keywords):
            if search:
                spinner_placeholder.info("Shopping ingredients now...")
                context = search_web(prompt)
            else:
                spinner_placeholder.empty()  # Clear the spinner if exiting early.
                return


    # Display the prompt and response in chat messages.
    st.chat_message("user").markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        llm_func = call_reasoning_llm if reasoning else call_llm
        spinner_placeholder.info("Cooking your response...")
        for response_chunk in llm_func(context=context, prompt=prompt, api_key=api_key):
            full_response += response_chunk
            message_placeholder.markdown(full_response + "| ")
        message_placeholder.markdown(full_response)
    spinner_placeholder.empty()


# Main: Create the streamlit web application
if __name__ == '__main__':
    st.set_page_config(page_title="S&CA AI Pilot", layout="wide")
    
    create_users_table()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state.get("authenticated"):
        if "logout" in st.query_params:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()

        total_cost = get_user_cost(st.session_state["username"])
        month = datetime.now().strftime("%B")
        st.markdown(
            f"""
            <style>
            .user-dropdown {{
                position: fixed;
                top: 10px;
                left: 10px;
                z-index: 999999999;
            }}
            .user-dropdown img {{
                width: 30px;
                height: 30px;
                border-radius: 50%;
                cursor: pointer;
                background: white;
                padding: 5px;
            }}
            .user-dropdown .dropdown-content {{
                display: none;
                position: absolute;
                background: #2f2f2f;
                width: 200px;
                box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.3);
                padding: 5px;
            }}
            .user-dropdown:hover .dropdown-content {{
                display: block;
                cursor: pointer;
                z-index: 999999999;
            }}
            .dropdown-content a, .dropdown-content p {{
                text-decoration: none;
                color: white;
                font-size: 0.8rem;
                margin: 0;    
            }}
            </style>
            <div class="user-dropdown">
                <img src="https://img.icons8.com/ios-filled/30/000000/user.png" alt="User Icon"/>
                <div class="dropdown-content">
                    <p>{st.session_state['username']}</p>
                    <p>Usage - {month}: ${total_cost:.2f}</p>
                    <a href="?logout=1" target = "_parent">Logout</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not st.session_state["authenticated"]:
        st.markdown("""
            <style>
            .centered {
                text-align: center;
            }
            </style>
            <h1 class="centered">Welcome to the AI-Powered App</h1>""", 
            unsafe_allow_html=True
        )
        col1, col2, col3, col4 = st.columns([5, 1, 1, 5])

        with col2:
            if st.button("Login"):
                st.session_state["page"] = "Login"

        with col3:
            if st.button("Sign Up"):
                st.session_state["page"] = "Sign Up"

        if st.session_state.get("page") == "Login":
            col1, col2, col3 = st.columns([4, 4, 4])
            with col2:
                st.subheader("Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Sign In"):
                    if verify_user(username, password):
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.success("Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    elif username == "admin" and password == "mysecpwd":
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.success("Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        elif st.session_state.get("page") == "Sign Up":
            col1, col2, col3 = st.columns([4, 4, 4])
            with col2:
                st.subheader("Sign Up")
                new_username = st.text_input("Create a Username")
                new_password = st.text_input("Create a Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                if st.button("Sign Up Now"):
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long!")
                    else:
                        add_user(new_username, new_password)   
                        st.success("User created successfully!") 
                        time.sleep(1)
                        st.session_state["page"] = "Login"
                        st.rerun()
        st.stop()


    if "chat_sessions" not in st.session_state:
        username = st.session_state.get("username", "default")
        st.session_state.chat_sessions = load_chat_sessions(username)

    if not st.session_state.chat_sessions:
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat_sessions.append({
            "chat_id": new_chat_id,
            "title": "New Chat",
            "messages": []
        })
        save_chat_sessions(st.session_state.chat_sessions, username)
        
    elif "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = st.session_state.chat_sessions[0]["chat_id"]

    with st.sidebar:
        st.header("Chat History")

        # Chat session selector
        chat_mapping = {chat["chat_id"]: chat["title"] for chat in st.session_state.chat_sessions}
        selected_title = st.sidebar.selectbox("Select Chat", list(chat_mapping.values()))
        # Set current_chat_id based on selected title
        for chat_id, title in chat_mapping.items():
            if title == selected_title:
                st.session_state.current_chat_id = chat_id
                break
        
        col1, col2 = st.columns([1, 1])

        button_style = """
            <style>
            .stButton>button {
                width: 120px; 
                border: 0.8px solid rgba(255, 255, 255, 0.3); 
                border-radius: 12px; 
                cursor: pointer;
            }
            </style>
        """

        # Inject custom CSS into the Streamlit app
        st.markdown(button_style, unsafe_allow_html=True)

        with col1:
            if st.button("New Chat"):
                new_chat_id = str(uuid.uuid4())
                new_title = f"New Chat {len(st.session_state.chat_sessions)+1}"
                st.session_state.chat_sessions.append({
                    "chat_id": new_chat_id,
                    "title" : new_title,
                    "messages": []
                })
                st.session_state.current_chat_id = new_chat_id
                save_chat_sessions(st.session_state.chat_sessions, st.session_state.username)
                st.rerun()

        with col2:
            if st.button("Delete"):
                # Remove the current chat from the sessions list
                chat_to_delete = st.session_state.current_chat_id
                username = st.session_state.get("username")
                if username != "admin":
                    temp_store_path = f"rag_chroma_temp_user_{username}_{chat_to_delete}"
                    if os.path.exists(temp_store_path):
                        shutil.rmtree(temp_store_path)
                st.session_state.chat_sessions = [
                    chat for chat in st.session_state.chat_sessions if chat["chat_id"] != chat_to_delete
                ]
                save_chat_sessions(st.session_state.chat_sessions, username)
                # Update current_chat_id
                if st.session_state.chat_sessions:
                    st.session_state.current_chat_id = st.session_state.chat_sessions[0]["chat_id"]
                else:
                    # If no sessions remain, create a new default session
                    new_chat_id = str(uuid.uuid4())
                    st.session_state.current_chat_id = new_chat_id
                    st.session_state.chat_sessions.append({
                        "chat_id": new_chat_id,
                        "title": "New Chat",
                        "messages": []
                    })
                save_chat_sessions(st.session_state.chat_sessions, username)
                st.success("Chat deleted successfully!")
                st.rerun()

    st.header("S&CA AI Pilot")
    
    chat_container = st.container(key="mainContainer")
    st.markdown(
            f"""
            <style>
                .mainContainer{{height: calc(100vh - 120px);
                overflow-y: auto;
                padding-bottom: 80px;
            }}
                .stChatMessageContent div[data-testid="stMarkdownContainer"] {{
                    overflow-wrap: break-word;
                    word-break: break-word;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )
    with chat_container:
        current_chat = next((chat for chat in st.session_state.chat_sessions
        if  chat["chat_id"] == st.session_state.current_chat_id), None)

        if current_chat:
            for message in current_chat["messages"]:
                st.chat_message("user").markdown(message["question"])
                st.chat_message("assistant").markdown(message["answer"])

        else:
            st.write("")

    if "thinking" not in st.session_state:
        st.session_state.thinking = False
    if "search" not in st.session_state:
        st.session_state.search = False

    # Place the custom buttons in your layout
    with stylable_container(
        key="bottomContent", 
        css_styles="""
            {
                position: fixed;
                align-content: center;
                bottom: 30px;
                color: rgba(255, 255, 255, 0.6);
                z-index: 99999999;
            }
        """):
        
        prompt = st.chat_input("How may I help you?", accept_file=True, file_type=["pdf", "docx", "text", "csv", "xls", "xlsx", "xlsm"], disabled=False)

        col1, col2, col3 = st.columns([1, 1, 6])


        # Use different button colors based on state
        thinking_type = "primary" if st.session_state.thinking else "secondary"
        search_type = "primary" if st.session_state.search else "secondary"
        
        if col1.button("💡 Reason", key="toggle_thinking", type=thinking_type):
            st.session_state.thinking = not st.session_state.thinking
            st.rerun()
            
        if col2.button("🔍 Search", key="toggle_search", type=search_type):
            st.session_state.search = not st.session_state.search
            st.rerun()

    # Process file input first, if any
    if prompt and prompt.get("files") and prompt.get('text'):
        uploaded_file = prompt["files"][0]
        normalize_uploaded_file_name = uploaded_file.name.translate(
            str.maketrans({"-": "_", ".": "_", " ": "_"})
        )
        all_splits, file_size_bytes = process_document(uploaded_file)

        if st.session_state.get("username") == "admin":
                store_path = "rag-chroma-main"
                collection_name = "sca-rag-pilot-main"
        else:
            username = st.session_state.get("username")
            chat_id = st.session_state.current_chat_id
            store_path = f"rag_chroma_temp_{username}_{chat_id}"
            collection_name = f"sca_rag_temp_{username}_{chat_id}"
        add_to_collection(all_splits, normalize_uploaded_file_name, file_size_bytes, api_key, store_path, collection_name)
        query_and_display_response(prompt["text"], reasoning=st.session_state.thinking, search=st.session_state.search)


    if prompt and prompt.get('text'):
        query_and_display_response(prompt["text"], reasoning=st.session_state.thinking, search=st.session_state.search)

    with stylable_container(
        key="bottom_content", 
        css_styles="""
            {
                position: fixed;
                bottom: 5px;
                left: 45%;
                color: rgba(255, 255, 255, 0.6);
                z-index: 99999999;
            }
        """
    ):
        st.markdown('<span style="font-size: 0.8rem; font-family: Cambria">This chatbot can make mistakes. Check for important info.</span>', 
        unsafe_allow_html = True)
