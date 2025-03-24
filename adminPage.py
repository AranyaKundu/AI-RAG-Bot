import streamlit as st
import os
from fileprocessing import process_document, process_zip
from vectordb import add_to_collection
from uservalidate import get_user_cost
from styles import (
    get_main_styles, 
    get_sidebar_button_styles, 
    get_user_dropdown_styles
)
from datetime import datetime

# Get the API Key
api_key = st.secrets["api_keys"]["openai"]

def admin_page(username):
    """Admin page with document management functionality"""
    
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
    
    # Main layout
    st.title("Admin Dashboard")
    st.subheader(f"Welcome, {username}")
    
    # Sidebar for admin controls
    with st.sidebar:
        st.header("Admin Controls")
        
        # Document upload section
        st.subheader("Document Management")
        
        # Multiple file upload
        uploaded_files = st.file_uploader("Upload Documents", 
                                         type=["pdf", "docx", "txt", "csv", "xls", "xlsx", "xlsm"],
                                         key="admin_file_uploader",
                                         accept_multiple_files=True)
        process_button = st.button("Process All Files", key="process_documents")
        
        if uploaded_files and process_button:
            with st.spinner("Processing documents..."):
                success_count = 0
                failure_count = 0
                
                for uploaded_file in uploaded_files:
                    normalize_uploaded_file_name = uploaded_file.name.translate(
                        str.maketrans({"-": "_", ".": "_", " ": "_"})
                    )
                    
                    # Process the document and split it into chunks
                    all_splits, file_size_bytes = process_document(uploaded_file)
                    
                    if all_splits and file_size_bytes > 0:
                        # Admin documents always go to the main collection
                        store_path = "rag-chroma-main"
                        collection_name = "sca-rag-pilot-main"
                        
                        # Add document chunks to vector store collection
                        add_to_collection(all_splits, normalize_uploaded_file_name, 
                                            file_size_bytes, api_key, store_path, collection_name)
                        success_count += 1
                    else:
                        failure_count += 1
                
                if success_count > 0:
                    st.success(f"✅ Successfully processed {success_count} files to the main knowledge base!")
                if failure_count > 0:
                    st.error(f"Failed to process {failure_count} files. Please check file formats.")
    
    # Main content area
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Usage Statistics")
        st.info("Usage statistics feature coming soon.")
        
    with col2:
        st.subheader("System Status")
        st.success("System is running normally")
        
    st.subheader("Knowledge Base Management")
    st.write("This section allows you to manage the main knowledge base for all users.")
    

    if st.button("Logout", key="admin_logout"):
        return "logout"
    
    return None