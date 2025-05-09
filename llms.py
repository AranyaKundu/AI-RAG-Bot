import streamlit as st
import requests, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
# LLM Import
from openai import OpenAI
from uservalidate import update_user_cost
from chatFunctions import append_message_to_current_chat

# Instruction prompt for the AI assistant
system_prompt_generic = """
    You are an AI assistant tasked with providing detailed answers based on the given context. Your goal is to analyze the information provided and formulate a comprehensive, well-structured response to the question.

    context will be passed in as "Context:"
    user question will be passed in as "Question:"

    To answer the question:
    1. Thoroughly analyze the context, which includes a combination of:
        - Uploaded files in the prompt
        - Text in the prompt  
        - Relevant documents from our knowledge base
        - Potentially web search results
        - And occasionally website crawl data
    2. Order of priority of context:
        - If there is a file uploaded with prompt, the file gets highest priority for context.
        - The text in the prompt gets 2nd highest priority.
        - For website crawling, website information gets highest priority.
        - Latest information has higher order of priority over older information.
    3. Always prioritize information from the knowledge base (context) over your general knowledge.
    4. When the context contains information from multiple sources, synthesize it into a coherent answer.
    5. If the context contains web search results or crawled website data, explicitly mention the source of information.
    6. If the question asks about something not covered in the context, clearly state the limitations and then provide information from your general knowledge, clearly indicating when you're doing so.
    7. Ensure that your answer addresses all aspects of the user's question directly and comprehensively.

    Format your response as follows:
    1. Use clear, professional language with concise paragraphs.
    2. Organize complex information using bullet points or numbered lists where appropriate.
    3. Include relevant headings or subheadings for structured responses on complex topics.
    4. Keep your tone professional and helpful at all times.
    5. When citing information from specific sources, clearly reference them.
    6. Use markdown formatting to improve readability when appropriate.

    Remember: Always base your response primarily on information in the provided context following the order of priority of the context, using your general knowledge only when the context is insufficient, and clearly indicate when you're doing so.
"""

system_prompt_reasoning = """
    You are an AI assistant tasked with providing detailed answers based on the given context and your general knowledge. Your goal is to analyze the context and the information provided and formulate a comprehensive, well-structured response to the question.

    context may include an uploaded file, a web search, or a website crawl. Summarize the context in a concise manner before answering the question.
    context will be passed in as "Context:"
    user question will be passed in as "Question:"

    To answer the question:
    1. Thoroughly analyze the context, which includes a combination of:
        - Uploaded files in the prompt
        - Text in the prompt 
        - Relevant documents from our knowledge base
        - Potentially web search results
        - And occasionally website crawl data
    2. Order of priority of context:
        - If there is a file uploaded with prompt, the file gets highest priority for context.
        - The text in the prompt gets 2nd highest priority.
        - For website crawling, website information gets highest priority.
        - Latest information has higher order of priority over older information.
    3. Always prioritize information from the knowledge base (context) over your general knowledge.
    4. When the context contains information from multiple sources, synthesize it into a coherent answer.
    5. If the context contains web search results or crawled website data, explicitly mention the source of information.
    6. If the question asks about something not covered in the context, clearly state the limitations and then provide information from your general knowledge, clearly indicating when you're doing so.
    7. Ensure that your answer addresses all aspects of the user's question directly and comprehensively.
    8. If the context includes a combination of sources, explicitly mention the source of information for each source.
    9. If the context includes a combination of sources, synthesize the information into a coherent answer.
    10. If the context includes a combination of sources, except web search, use your general knowledge to supplement the information from the context.
    11. If the context includes a combination of sources, clearly indicate when you're doing so.
    12. If the context includes a combination of sources, clearly indicate when you're doing so.

    Format your response as follows:
    1. Use clear, professional language with concise paragraphs.
    2. Organize complex information using bullet points or numbered lists where appropriate.
    3. Include relevant headings or subheadings for structured responses on complex topics.
    4. Keep your tone professional and helpful at all times.
    5. When citing information from specific sources, clearly reference them.
    6. Use markdown formatting to improve readability when appropriate.
    7. If the context includes a website crawl, explicitly mention the source of information.
    8. If the context includes a web search, explicitly mention the source of information.
    9. If the context includes an uploaded file, explicitly mention the source of information.

    Remember: Always base your response primarily on information in the provided context following the order of priority of the context, using your general knowledge only when the context is insufficient, and clearly indicate when you're doing so.
"""


# Call the llm model: chat completions endpoint: import openai
def call_llm(context: str, prompt: str, api_key, temperature=0.1):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature = temperature,
        messages=[
            {"role": "developer", "content": system_prompt_generic},
            {"role": "user", "content": f"Context: {context}\nQuestion: {prompt}"}
        ], 
        max_tokens=1000,
        stream=True,
        stream_options={"include_usage": True}
    )
    cost_per_output_token = 0.6/10**6 # ChatGPT 4o-mini Output tokens pricing (this is on the higher end, input tokens are cheaper 0.15/1M tokens)
    cost_per_prompt_token = 0.15/ 10**6
    cost_incurred = 0
    
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
            yield chunk.choices[0].delta.content
        elif chunk.choices == []:
            prompt_tokens_count = chunk.usage.prompt_tokens
            completion_tokens_count = chunk.usage.completion_tokens
            cost_incurred += completion_tokens_count * cost_per_output_token + prompt_tokens_count * cost_per_prompt_token
            yield cost_incurred
        else:
            break
    
    update_user_cost(st.session_state["username"], cost_incurred)

# Reasoning LLM
def call_reasoning_llm(context: str, prompt: str, api_key: str, temperature=0.1):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model = "o3-mini",
        messages=[
            {'role': 'developer', 'content': system_prompt_reasoning},
            {"role": "user", "content": f"Context: {context}\nQuestion: {prompt}"}
        ],
        max_completion_tokens=1000,
        stream=True,
        stream_options= {"include_usage": True}
    )
    
    cost_per_output_token = 4.4/10**6 # ChatGPT 4o is one of the most advanced API Models with very high pricing. Do not use, until absolutely needed.
    cost_per_prompt_token = 1.10
    full_response = ""
    cost_incurred = 0

    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
            yield chunk.choices[0].delta.content
        elif chunk.choices == []:
            prompt_tokens_count = chunk.usage.prompt_tokens
            completion_tokens_count = chunk.usage.completion_tokens
            cost_incurred += completion_tokens_count * cost_per_output_token + prompt_tokens_count * cost_per_prompt_token
            yield cost_incurred
        else:
            break
    
    update_user_cost(st.session_state["username"], cost_incurred)


def generate_images(prompt: str, api_key: str):
    """
    Generate an image based on the given prompt using DALL-E 3.
    
    Args:
        prompt: Text description of the image to generate
        api_key: OpenAI API key
        
    Returns:
        str: URL of the generated image
    """
    try:
        client = OpenAI(api_key=api_key)

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        image_url = response.data[0].url
        
        # Calculate approximate cost (DALL-E 3 1024x1024 costs about $0.04 per image)
        cost_incurred = 0.04
        update_user_cost(st.session_state["username"], cost_incurred)
        
        return image_url
    except Exception as e:
        print(f"Error generating image: {e}")
        raise e


def search_web(query: str):
    """
    Search the web for information related to the query using Google Custom Search.
    Falls back to a secondary method if the primary search fails.
    Args:
        query: The search query
    Returns:
        A string containing the search results
    """
    try:
        # Primary search method - Google Custom Search API
        search_url = "https://customsearch.googleapis.com/customsearch/v1"
        params = {
            "key": 'AIzaSyCPuGi91baYB2dc9z2lQsSThV0RwX3iP1Y',
            "cx": '3256360bd259a492b',  
            "q": query,
            "num": 5  # Request 5 results
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        search_results = response.json()

        if "items" in search_results and search_results["items"]:
            results = search_results["items"]
            answer = f"Web search results for: '{query}'\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                snippet = result.get('snippet', 'No description available')
                link = result.get('link', '#')
                answer += f"**{i}. {title}**\n{snippet}\nSource: {link}\n\n"
            
            return answer
        else:
            # If no results from primary method, try secondary method
            return fallback_search(query)
    
    except Exception as e:
        print(f"Error in primary search: {e}")
        # Fall back to secondary search method
        return fallback_search(query)

def fallback_search(query: str):
    """Fallback search method using DuckDuckGo"""
    try:
        # Simple HTML scraping as fallback (add proper handling for rate limits)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result')
        
        if results:
            answer = f"Web search results for: '{query}'\n\n"
            for i, result in enumerate(results[:5], 1):
                title_element = result.find('a', class_='result__a')
                title = title_element.text.strip() if title_element else "No title"
                
                snippet_element = result.find('a', class_='result__snippet')
                snippet = snippet_element.text.strip() if snippet_element else "No description available"
                
                link = title_element['href'] if title_element and 'href' in title_element.attrs else "#"
                
                answer += f"**{i}. {title}**\n{snippet}\nSource: {link}\n\n"
            
            return answer
        
        # If both methods fail, return this message
        return "No external search results found. I'll answer based on my training."
    
    except Exception as e:
        print(f"Error in fallback search: {e}")
        return "Web search functionality is currently unavailable. I'll answer based on my training."

def crawl_website(base_url: str, max_depth: int = 1, delay: float = 1.0):
    """
    Crawl a specific website starting from base_url.
    Parameters:
      base_url (str): The starting URL.
      max_depth (int): How deep to crawl. Default is 1 (only the base page).
      delay (float): Delay between requests to be polite.
    
    Returns:
      dict: A dictionary mapping URLs to their text content.
    """
    visited = set()
    results = {}

    def crawl(url, depth):
        if depth > max_depth:
            return
        if url in visited:
            return
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            visited.add(url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            results[url] = text
            
            # Find all internal links and crawl them recursively
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Normalize relative links
                absolute_url = urljoin(url, href)
                # Ensure we only crawl links within the same domain
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                    crawl(absolute_url, depth + 1)
            time.sleep(delay)
        except Exception as e:
            print(f"Error crawling {url}: {e}")

    crawl(base_url, 0)
    return results


