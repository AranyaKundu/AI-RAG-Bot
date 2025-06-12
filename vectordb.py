import streamlit as st
# vector database
import chromadb
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction
from langchain_core.documents import Document
import os


# Create the vector collection: import chromadb
def get_vector_collection(api_key: str, store_path: str, collection_name: str) -> chromadb.Collection:
    openai_ef = OpenAIEmbeddingFunction(
        api_key=api_key, model_name="text-embedding-3-small"
    )
    try:
        # embedding_function = create_cached_embedding_function(api_key)
        chroma_client = chromadb.PersistentClient(path=store_path)
        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=openai_ef,
            metadata={"hnsw:space": "cosine"}
        )
        return collection

    except Exception as e:
        st.error(f"ChromaDB connection test failed: {e}")
        raise e


# Add to vector collection
def add_to_collection(all_splits: list[Document], file_name: str, file_size_bytes: float, api_key: str, store_path: str, collection_name: str):  
    """
    Add document splits to vector collection.
    
    Args:
        all_splits: List of Document objects to add
        file_name: Name of the file being processed
        file_size_bytes: Size of the file in bytes
        api_key: OpenAI API key for embeddings
        store_path: Path to store the vector collection
        collection_name: Name of the collection
    """
    if not all_splits:
        st.warning("No content to add to vector store.")
        return
        
    collection = get_vector_collection(api_key, store_path, collection_name)
    num_splits = len(all_splits)
    kb_500 = 500 * 1024
    num_batches = max(1, (file_size_bytes + kb_500 - 1) // kb_500)
    dynamic_batch_size = num_splits // num_batches if num_batches > 0 else num_splits 

    for i in range(0, num_splits, dynamic_batch_size):
        batch_splits = all_splits[i:i + dynamic_batch_size]
        # Extract content and metadata from Document objects
        batch_documents = [split.page_content for split in batch_splits]
        batch_metadatas = [split.metadata for split in batch_splits]
        batch_ids = [f"{file_name}_{idx}" for idx in range(i, i + len(batch_splits))]
        batch_num = i // dynamic_batch_size + 1

        try:
            collection.upsert(
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids,
            )
            print(f"Batch {batch_num}/{(num_splits + dynamic_batch_size - 1) // dynamic_batch_size} added successfully.")
        except Exception as e:
            st.error(f"Error upserting batch {batch_num}: {e}")
            raise



# Query the vector collection: semantic search algorithm
def query_collection(prompt: str, api_key: str, n_results=10):
    # First, try to get results from the main collection
    try:
        main_collection = get_vector_collection(api_key, store_path="rag-chroma-main", collection_name="sca-rag-pilot-main")
        main_results = main_collection.query(query_texts=[prompt], n_results=n_results)
        main_docs = main_results.get("documents", [[]])[0]
    except Exception as e:
        st.warning(f"Error querying main collection: {e}")
        main_docs = []
    
    # For non-admin users, also query their temporary collection
    if st.session_state.get("username") != "admin":
        try:
            username = st.session_state.get("username")
            chat_id = st.session_state.current_chat_id
            store_path = f"rag_chroma_temp_{username}_{chat_id}"
            collection_name = f"sca_rag_temp_{username}_{chat_id}"
            
            # Check if the temporary collection exists before querying
            if os.path.exists(store_path):
                temp_collection = get_vector_collection(api_key, store_path=store_path, collection_name=collection_name)
                temp_results = temp_collection.query(query_texts=[prompt], n_results=n_results)
                temp_docs = temp_results.get("documents", [[]])[0]
            else:
                temp_docs = []
        except Exception as e:
            st.warning(f"Error querying temporary collection: {e}")
            temp_docs = []
        
        # Combine documents from both collections
        combined_docs = main_docs + temp_docs
    else:
        combined_docs = main_docs
    
    # Calculate relevance scores and sort by most relevant
    if combined_docs:
        # Filter out empty documents and deduplicate
        filtered_docs = []
        seen_content = set()
        for doc in combined_docs:
            doc_content = doc.strip()
            if doc_content and doc_content not in seen_content:
                filtered_docs.append(doc_content)
                seen_content.add(doc_content)
        
        combined_results = {"documents": [filtered_docs]}
        return combined_results
    else:
        return {"documents": [["No relevant information found in the knowledge base."]]}