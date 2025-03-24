import re
import streamlit as st
from chatFunctions import save_chat_sessions, delete_chat
from vectordb import query_collection
from llms import call_llm, call_reasoning_llm, search_web, crawl_website, generate_images
from styles import get_latex_styles
from fileprocessing import process_document

# Get the API Key
api_key = st.secrets["api_keys"]["openai"]


def get_reasoning_context(prompt):
    """
    Generate additional context for the reasoning model.
    If the prompt includes an uploaded document, summarize its contents.
    Otherwise, use the prompt text combined with the vector collection context.
    """
    # Extract text prompt
    prompt_text = prompt.get("text") if isinstance(prompt, dict) else prompt
    
    # Query the vector store for additional context
    results = query_collection(prompt_text, api_key)
    documents = results.get("documents")
    vector_context = "\n\n".join(documents[0]) if documents and len(documents) > 0 and documents[0] else ""
    
    # Check if there's an uploaded file in the prompt (if prompt is a dict)
    if isinstance(prompt, dict) and prompt.get("files"):
        # Process the first uploaded file
        uploaded_file = prompt["files"][0]
        all_splits, _ = process_document(uploaded_file)
        # Combine the document chunks into one string
        doc_text = "\n".join([doc.page_content for doc in all_splits])
        # Summarize the document text
        summary = summarize_text(doc_text, api_key)
        return f"Document Summary:\n{summary}\n\nAdditional Context:\n{vector_context}"
    else:
        # If no file was uploaded, use vector store context
        if vector_context:
            return f"Knowledge Base Information:\n{vector_context}"
        else:
            return "No additional context found in knowledge base."

def summarize_text(context: str, api_key: str):
    """
    Summarize the provided text using an LLM summarization model.
    For this example, we'll simply return the first 1000 characters.
    """
    # Ensure the text is not excessively long for a summary placeholder.
    prompt = "Create a summary of the document in 1000 words or less"
    summary = call_llm(context= context, prompt= prompt, api_key=api_key, temperature=1.0)
    summary = summary[:1000] + "..." if len(summary) > 1000 else summary
    return summary



# App specific codes: Design & Additional Features
def query_and_display_response(prompt, reasoning=False, search=False, images=False):
    if images:
        reasoning = False
        search = False
    
    # Create placeholders for UI feedback
    spinner_placeholder = st.empty()
    spinner_message = "Inventing Recipe..." if reasoning else "Analyzing Recipe..." if search else "Generating Image..." if images else "Thinking..."
    spinner_placeholder.info(spinner_message)
    st.chat_message("user").markdown(prompt)
    
    # Default context
    context = "No relevant information found in the knowledge base."
    
    # Check if the prompt contains URLs for crawling
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    urls = url_pattern.findall(prompt)
    
    # Handle image generation separately (simplest case)
    if images:
        context = prompt
    # Handle URL crawling if URLs found and search is enabled
    elif urls and len(urls) > 0 and search:
        spinner_placeholder.info(f"Crawling websites: {urls[0]}...")
        crawl_results = crawl_website(urls[0], max_depth=1)
        if crawl_results:
            crawled_context = "\n\n".join([f"From {url}: {content[:1000]}..." for url, content in crawl_results.items()])
            context = crawled_context
    # Handle URL found but search not enabled
    elif urls and len(urls) > 0 and not search:
        context = "URLs found in the prompt, but search is not enabled."
    # Handle reasoning with vector store context
    elif reasoning:
        spinner_placeholder.info("Building reasoning context...")
        knowledge_base = get_reasoning_context(prompt)
        context = prompt + "\n\n" + knowledge_base
    # Otherwise query vector store for regular queries
    else:
        # Query vector store
        results = query_collection(prompt, api_key)
        documents = results.get("documents")
        context_list = documents[0] if documents and len(documents) > 0 and documents[0] else []
        
        if context_list and len(context_list) > 0:
            combined_context = "\n\n".join(context_list)
            if "insufficient information" not in combined_context.lower() and "does not contain any information" not in combined_context.lower():
                context = combined_context
    
    # Handle web search if needed and not images mode
    if (context == "No relevant information found in the knowledge base." or search) and not urls and not images:
        spinner_placeholder.info("Searching the web for information...")
        web_context = search_web(prompt)
        if web_context and "No external search results found" not in web_context:
            # Combine vector store results with web search if both are available
            if context != "No relevant information found in the knowledge base.":
                context = f"{context}\n\nAdditional information from web:\n{web_context}"
            else:
                context = web_context

    # --- Response generation phase ---
    # Add LaTeX styles to enable proper formula rendering
    st.markdown(get_latex_styles(), unsafe_allow_html=True)
    
    # Display the chat message from assistant
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Generate image if in image mode
        if images:
            spinner_placeholder.info("Drawing the masterpiece...")
            try:
                image_url = generate_images(prompt=prompt, api_key=api_key)
                # Display the image without text
                message_placeholder.image(image_url, caption=None, use_container_width=True)
                full_response = f"![Generated Image]({image_url})"
            except Exception as e:
                full_response = f"Sorry, I couldn't generate an image. Error: {str(e)}"
                message_placeholder.error(full_response)
        # Handle text response with appropriate LLM
        else:
            full_response = ""
            # Choose the right LLM based on reasoning flag
            llm_func = call_reasoning_llm if reasoning else call_llm
            spinner_placeholder.info("Cooking your response...")
            
            # Process LaTeX in response during streaming
            for response_chunk in llm_func(context=context, prompt=prompt, api_key=api_key, temperature=st.session_state.temperature):
                full_response += response_chunk
                # Use a different approach for displaying the streaming content
                message_placeholder.markdown(full_response + "| ", unsafe_allow_html=True)
            
            # Extra processing for reasoning model to ensure markdown works correctly
            if reasoning:
                # Clear the placeholder first
                message_placeholder.empty()
                # Then render the full response with unsafe_allow_html set to True
                message_placeholder.markdown(full_response, unsafe_allow_html=True)
            else:
                # Format final response for regular LLM
                message_placeholder.markdown(full_response, unsafe_allow_html=True)
        
        # Save chat message
        if "current_chat_id" in st.session_state and st.session_state.chat_sessions:
            current_chat = next((chat for chat in st.session_state.chat_sessions if chat["chat_id"] == st.session_state.current_chat_id), None)
            if current_chat:
                current_chat["messages"].append({"question": prompt, "answer": full_response})
                save_chat_sessions(st.session_state.chat_sessions, st.session_state.username)
                
    spinner_placeholder.empty()


def handle_chat_button(chat, is_active, button_label, update_favorite):
    chat_id = chat["chat_id"]
    body = chat["title"]

    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        # Use a single button call with dynamic type
        btn_type = "tertiary" if is_active else "secondary"
        if st.button(body, key=f"chat_{chat_id}", type=btn_type):
            st.session_state.current_chat_id = chat_id
            st.rerun()

    with col2:
        if st.button(button_label, key=f"fav_{chat_id}"):
            chat["favorite"] = update_favorite
            save_chat_sessions(st.session_state.chat_sessions, st.session_state.username)
            st.rerun()
    
    with col3:
        if st.button("🗑️", key=f"del_{chat_id}"):
            delete_chat(chat_id)
