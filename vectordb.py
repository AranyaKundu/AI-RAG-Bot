import streamlit as st
# vector database
import chromadb
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction
from langchain_core.documents import Document


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
    collection = get_vector_collection(api_key, store_path, collection_name)
    num_splits = len(all_splits)
    kb_500 = 500 * 1024
    num_batches = max(1, (file_size_bytes + kb_500 - 1) // kb_500)
    dynamic_batch_size = num_splits // num_batches if num_batches > 0 else num_splits 

    for i in range(0, num_splits, dynamic_batch_size):
        batch_splits = all_splits[i:i + dynamic_batch_size]
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
        except Exception as e:
            st.error(f"Error upserting batch {batch_num}: {e}")
            raise



# Query the vector collection
def query_collection(prompt: str, api_key: str, n_results=10):
    main_collection = get_vector_collection(api_key, store_path="rag-chroma-main", collection_name="sca-rag-pilot-main")    
    main_results = main_collection.query(query_texts=[prompt], n_results=n_results)
    if st.session_state.get("username") == "admin":
        return main_results
    else:
        username = st.session_state.get("username")
        chat_id = st.session_state.current_chat_id
        temp_collection = get_vector_collection(api_key, store_path=f"rag_chroma_temp_{username}_{chat_id}", collection_name=f"sca_rag_temp_{username}_{chat_id}")
        temp_results = temp_collection.query(query_texts=[prompt], n_results=n_results)
        # combine main and temporary documents
        combined_docs = main_results.get("documents")[0] + temp_results.get("documents")[0]
        combined_results = {"documents": [combined_docs]}
        return combined_results