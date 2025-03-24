import re
import streamlit as st
from chatFunctions import save_chat_sessions, delete_chat
from vectordb import query_collection
from llms import call_llm, call_reasoning_llm, search_web, crawl_website, generate_images
from styles import get_latex_styles


# Get the API Key
api_key = st.secrets["api_keys"]["openai"]


# App specific codes: Design & Additional Features
def query_and_display_response(prompt, reasoning=False, search=False, images=False):
    # Check if the prompt contains a URL for crawling
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    urls = url_pattern.findall(prompt)
    
    # Default context
    context = "No relevant information found in the knowledge base."
    
    # Always query the vector store first
    results = query_collection(prompt, api_key)
    documents = results.get("documents")
    context_list = documents[0] if documents and len(documents) > 0 and documents[0] else []
    
    spinner_placeholder = st.empty()
    spinner_message = "Inventing Recipe..." if reasoning else "Analyzing Recipe..." if search else "Generating Image..." if images else "Thinking..."
    spinner_placeholder.info(spinner_message)
    st.chat_message("user").markdown(prompt)

    # If URL is found in the prompt, crawl the website and search is true
    if urls and len(urls) > 0 and search:
        spinner_placeholder.info(f"Crawling websites: {urls[0]}...")
        crawl_results = crawl_website(urls[0], max_depth=1)
        if crawl_results:
            # Combine crawled content into a single context
            crawled_context = "\n\n".join([f"From {url}: {content[:1000]}..." for url, content in crawl_results.items()])
            context = crawled_context
    elif urls and len(urls) > 0 and not search:
        spinner_placeholder.info(f"Thinking about searching the recipe...")
        context = "Urls found in the prompt, but search is not enabled."
    # If vector store has relevant documents, use them
    elif context_list and len(context_list) > 0:
        combined_context = "\n\n".join(context_list)
        if "insufficient information" not in combined_context.lower() and "does not contain any information" not in combined_context.lower():
            context = combined_context
    elif images:
        context = prompt
    
    # If we still need to search web (no vector store results or explicitly requested)
    if (context == "No relevant information found in the knowledge base." or search) and not urls and not images:
        spinner_placeholder.info("Searching the web for information...")
        web_context = search_web(prompt)
        if web_context and "No external search results found" not in web_context:
            # Combine vector store results with web search if both are available
            if context != "No relevant information found in the knowledge base.":
                context = f"{context}\n\nAdditional information from web:\n{web_context}"
            else:
                context = web_context


    # Add LaTeX styles to enable proper formula rendering
    st.markdown(get_latex_styles(), unsafe_allow_html=True)
    
    # Display the chat message from assistant
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        if images:
            # Handle image generation
            spinner_placeholder.info("Generating image based on your prompt...")
            try:
                image_url = generate_images(prompt=prompt, api_key=api_key)
                # Display the image without text
                message_placeholder.image(image_url, caption=None, use_container_width=True)
                full_response = f"![Generated Image]({image_url})"
            except Exception as e:
                full_response = f"Sorry, I couldn't generate an image. Error: {str(e)}"
                message_placeholder.error(full_response)
        else:
            # Handle text response with LLM
            full_response = ""
            llm_func = call_reasoning_llm if reasoning else call_llm
            spinner_placeholder.info("Cooking your response...")
            
            # Process LaTeX in response during streaming
            for response_chunk in llm_func(context=context, prompt=prompt, api_key=api_key, temperature=st.session_state.temperature):
                full_response += response_chunk
                message_placeholder.markdown(full_response + "| ", unsafe_allow_html=True)
            
            # Format final response for LaTeX rendering
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
    # st.markdown("""
    #         <style>
    #         .active-chat {
    #             background-color: #d1e7dd;
    #         }
    #         </style>
    #     """, unsafe_allow_html=True)

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
