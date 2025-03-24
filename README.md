# AI-RAG-Bot: Pilot Application

A Streamlit-based AI assistant that provides responsive, intelligent interactions. The application supports chat-based conversations, document processing, and knowledge retrieval.

## Features

- User authentication and session management
- Document processing (PDF, DOCX, TXT, Excel, CSV)
- OCR for scanned PDF documents
- Vector database for document storage and retrieval
- Web search integration
- Chat history with favorites
- LaTeX formula rendering
- Responsive design with custom styling

## File Structure

- `app.py` - Main application entry point
- `styles.py` - CSS styling and UI components
- `streamlitfunctions.py` - Core UI and interaction functions
- `fileprocessing.py` - Document processing and OCR
- `vectordb.py` - Vector database integration
- `chatFunctions.py` - Chat history management
- `llms.py` - LLM integration and reasoning
- `uservalidate.py` - User authentication
- `userPage.py` - Users Page in the Application - Visible after login
- `adminPage.py` - Admin Page in the Application - Visible after login as Admin

## Recent Updates

### Styling Improvements
- Moved all CSS to a dedicated `styles.py` file for better maintainability
- Fixed main container alignment to remain stable when sidebar opens
- Added active chat highlighting for better UX
- Added LaTeX formula rendering support

### PDF Processing Improvements
- Enhanced OCR capabilities for scanned PDFs
- Added fallback OCR mechanism using PyTesseract
- Improved error handling for document processing

### Code Organization
- Separated styling from functional code
- Improved error handling throughout the application
- Added better documentation

## Requirements

The application requires the following Python packages:
- streamlit
- langchain
- ocrmypdf
- pytesseract
- pymupdf (fitz)
- pandas
- openpyxl
- PIL

## Usage

To run the application:

```bash
streamlit run app.py
```

## Notes

- For PDF OCR to work properly, Tesseract OCR should be installed on the system
- API keys should be configured in Streamlit secrets 
