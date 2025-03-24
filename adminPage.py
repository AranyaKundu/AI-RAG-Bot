import streamlit as st
import os
from fileprocessing import process_document, process_folder, process_zip
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
        
        # Single file upload
        uploaded_file = st.file_uploader("Upload Document", 
                                         type=["pdf", "docx", "txt", "csv", "xls", "xlsx", "xlsm"],
                                         key="admin_file_uploader")
        process_button = st.button("Process", key="process_document")
        
        if uploaded_file and process_button:
            with st.spinner("Processing document..."):
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
                    st.success(f"✅ File '{uploaded_file.name}' processed and added to main knowledge base!")
                else:
                    st.error("Failed to process document. Please check file format.")
    
        # Folder path input for batch processing
        st.subheader("Batch Processing")
        # folder_path = st.text_input("Enter folder path to process", key="folder_path_input")
        folder_path = st.file_uploader("Upload ZIP Archive", type=["zip"])
        process_folder_button = st.button("Process Folder", key="process_folder_button")
        if folder_path and process_folder_button:
            # status = st.status("Processing ZIP archive...", expanded=True)
            # with status:
            #     total_files = 0
            #     success_count = 0
            #     for filename in process_zip(folder_path):
            #         total_files += 1
            #         with st.spinner(f"Processing {filename}"):
            #             try:
            #                 all_splits, file_size_bytes = process_document(filename)
            #                 if all_splits:
            #                     store_path = "rag-chroma-main"
            #                     collection_name = "sca-rag-pilot-main"
            #                     add_to_collection(all_splits, filename, file_size_bytes, api_key, store_path, collection_name)
            #                     success_count += 1
            #             except Exception as e:
            #                 st.error(f"Failed {filename}: {str(e)}")
        
            # status.update(label=f"✅ Processed {success_count}/{total_files} files", state="complete")
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                with st.spinner(f"Processing all files in {folder_path}..."):
                    try:
                        # Process folder and get all document splits
                        all_splits = process_folder(folder_path)
                        
                        if all_splits:
                            # Admin documents always go to the main collection
                            store_path = "rag-chroma-main"
                            collection_name = "sca-rag-pilot-main"
                            
                            # Add all document chunks to vector store collection
                            add_to_collection(all_splits, f"folder_{os.path.basename(folder_path)}", 
                                             len(all_splits) * 500, api_key, store_path, collection_name)
                            st.success(f"✅ All files in folder '{folder_path}' processed and added to main knowledge base!")
                        else:
                            st.warning("No valid documents found in the folder.")
                    except Exception as e:
                        st.error(f"Error processing folder: {str(e)}")
            else:
                st.error("Invalid folder path. Please enter a valid directory path.")

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




        