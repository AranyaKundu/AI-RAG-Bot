import os, tempfile, ocrmypdf, openpyxl, fitz, pytesseract, io
import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from docx import Document as DocxDocument
from PIL import Image
from pyunpack import Archive
import patoolib
# Langchain imports
from langchain_community.document_loaders import PyMuPDFLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Process documents for the user: import os, tempfile, pandas, langchain_text_splitters, langchain_core.documents, PyMuPDFLoader, Document
def process_document(uploaded_file: UploadedFile) -> tuple:
    """
    Process various document types and split them into chunks for vector storage.
    
    Args:
        uploaded_file: The uploaded file to process
        
    Returns:
        A tuple containing (all_splits, file_size_bytes)
    """
    # Store uploaded file as a temp file before it goes to vector database
    file_extension = uploaded_file.name.split(".")[-1].lower()
    temp_file = tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False)
    temp_file.write(uploaded_file.read())
    temp_file.seek(0)
    file_size_bytes = os.path.getsize(temp_file.name)
    temp_file.close()
    documents = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=100, separators=["\n\n", "\n", ".", "?", "!", " ", ""]
    )

    try:
        if file_extension == "docx":
            doc = DocxDocument(temp_file.name)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            documents.append(Document(page_content=text, metadata={"source": uploaded_file.name}))
        elif file_extension == "pdf":
            try:
                # First try using OCRMyPDF to convert scanned images to searchable PDF
                ocr_pdf_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
                ocrmypdf.ocr(temp_file.name, ocr_pdf_path, rotate_pages=True, remove_background=True, 
                            language="eng", deskew=True, force_ocr=True)
                loader = PyMuPDFLoader(ocr_pdf_path)
                documents = loader.load()
                if not any(doc.page_content.strip() for doc in documents):
                    raise Exception("OCRMyPDF produced empty text")
            except Exception as e:
                # If OCRMyPDF fails, try manual OCR approach
                try:
                    doc = fitz.open(temp_file.name)
                    full_text = []
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        text = page.get_text()
                        if text.strip():
                            full_text.append(text)
                        else:
                            # Extract image and OCR it
                            pix = page.get_pixmap()
                            img_bytes = pix.tobytes("png")
                            path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                            if os.path.exists(path_to_tesseract):
                                img = Image.open(io.BytesIO(img_bytes)) 
                                pytesseract.tesseract_cmd = path_to_tesseract
                                text = pytesseract.image_to_string(img)
                                full_text.append(text)
                            else:
                                img = Image.open(io.BytesIO(img_bytes))
                                text = pytesseract.image_to_string(img)
                                full_text.append(text)
                    documents = [Document(page_content="\n".join(full_text), metadata={"source": uploaded_file.name})]
                    doc.close()
                except Exception as nested_e:
                    st.error(f"Error processing PDF: {str(e)}. Fallback OCR also failed: {str(nested_e)}")
                    os.unlink(temp_file.name)
                    return [], 0
            finally:
                if os.path.exists(ocr_pdf_path):
                    os.unlink(ocr_pdf_path)
        elif file_extension == "txt":
            with open(temp_file.name, "r", encoding="utf-8", errors="replace") as f:
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
        else:
            st.error(f"Unsupported file format: {file_extension}. Please upload a PDF, DOCX, TXT, Excel, or CSV file.")
            os.unlink(temp_file.name)
            return [], 0
    except Exception as e:
        st.error(f"Error processing {file_extension} file: {str(e)}")
        os.unlink(temp_file.name)
        return [], 0

    # Split documents into chunks
    all_splits = []
    if documents:
        splits_raw = text_splitter.split_documents(documents)
        # Extract content and filter out empty chunks
        all_splits = [Document(page_content=split.page_content.strip(), metadata=split.metadata) 
                    for split in splits_raw if split.page_content.strip()]
    
    # Clean up the temp file
    os.unlink(temp_file.name)
    
    return all_splits, file_size_bytes

def process_folder(folder_path: str) -> list:
    """
    Process all files in a folder and return a list of splits from all documents.
    
    Args:
        folder_path: The path to the folder to process
        
    Returns:
        A list of splits (all_splits) from all processed documents
    """
    all_splits = []
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        try:
            # Call process_document and extract the splits
            file_splits, file_size_bytes = process_document(UploadedFile(file_path))
            all_splits.extend(file_splits)
        except Exception as e:
            # Log the error and continue processing the next file
            st.warning(f"Error processing file '{file_name}': {e}")
    
    return all_splits, file_size_bytes

def process_zip(uploaded_zip):
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        
        Archive(zip_path).extractall(tmpdir)

        for files in os.walk(tmpdir):
            for file in files:
                yield file
    