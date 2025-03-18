import os, tempfile, openpyxl
import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from docx import Document as DocxDocument
from datetime import datetime
# Langchain imports
from langchain_community.document_loaders import PyMuPDFLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Process documents for the user: import os, tempfile, pandas, langchain_text_splitters, langchain_core.documents, PyMuPDFLoader, Document
def process_document(uploaded_file: UploadedFile) -> list[Document]:
    # Store uploaded file as a temp file before it goes to vector database
    file_extension = uploaded_file.name.split(".")[-1].lower()
    temp_file = tempfile.NamedTemporaryFile(suffix=f"{file_extension}", delete=False)
    temp_file.write(uploaded_file.read())
    temp_file.seek(0)
    file_size_bytes = os.path.getsize(temp_file.name)
    temp_file.close()
    documents = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=100, separators=["\n\n", "\n", ".", "?", "!", " ", ""]
    )

    if file_extension == "docx":
        doc = DocxDocument(temp_file.name)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        documents.append(Document(page_content=text, metadata={"source": uploaded_file.name}))
    elif file_extension == "pdf":
        loader = PyMuPDFLoader(temp_file.name)
        documents = loader.load()
    elif file_extension == "txt":
        with open(temp_file.name, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append(Document(page_content=text, metadata={"source": uploaded_file.name}))
    elif file_extension in ["xls", "xlsm", "xlsx"]: 
        excel_df = pd.read_excel(temp_file.name, sheet_name=None)
        for sheet_name, sheet_df in excel_df.items():
            text = sheet_df.to_csv(index=False)
            documents.append(Document(page_content=text, metadata={"source": f"{uploaded_file.name} - {sheet_name}"}))
    elif file_extension == "csv":
        csv_df = pd.read_csv(temp_file.name)
        text = csv_df.to_csv(index=False)
        documents.append(Document(page_content=text, metadata = {"source": uploaded_file.name}))
        all_splits = text_splitter.split_documents(documents)
        cleaned_splits = []
        for split in all_splits:
            cleaned_text = split.page_content.strip()
            if cleaned_text:
                cleaned_split = Document(page_content=cleaned_text, metadata=split.metadata)
                cleaned_splits.append(cleaned_split)
        all_splits = cleaned_splits
        os.unlink(temp_file.name) 
        return all_splits, file_size_bytes
    else:
        st.error("Unsupported file format. Please upload a PDF, Document, txt, Excel or CSV file.")
    
    os.unlink(temp_file.name) 
    all_splits = text_splitter.split_documents(documents)
    return all_splits, file_size_bytes