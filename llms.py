import streamlit as st
import requests, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
# LLM Import
from openai import OpenAI
from uservalidate import update_user_cost
from chatFunctions import append_message_to_current_chat

# Instruction prompt for the AI assistant
system_prompt = """
    You are an AI assistant tasked with providing detailed answers based on the given context. Your goal is to analyze the information provided and formulate a comprehensive, well-structured response to the question.

    context will be passed in as "Context:"
    user question will be passed in as "Question:"

    To answer the question:
    1. Thoroughly analyze the context, identifying key information relevant to the question.
    2. Organize your thoughts and plan your response to ensure a logical flow of information.
    3. Formulate a detailed answer that directly addresses the question, using the information provided in the context.
    4. Ensure your answer is comprehensive, covering all relevant aspects found in the context.
    5. If the context doesn't contain sufficient information to fully answer the question, clearly state this in your response. 
    6. Mention all assumptions made and indicate the need to search for external answers.
    7. Search for external answers including web search and formulate an answer. Do not take shortcuts, search the internet extensively and draft a response. 
    8. Clearly state the basis of your information.

    Format your response as follows:
    1. Use clear, concise and strictly professional language.
    2. Organize your answer into paragraphs for readability.
    3. Use bullet points or numbered lists where appropriate to break down complex information.
    4. If relevant, include any headings or subheadings to structure your response.
    5. Ensure proper grammar, punctuation, and spelling throughout your answer.
    6. Make sure to avoid any cuss words or unprofessional language.

    Important: Base your entire response on the information provided in the context. Include any external knowledge or assumptions only after searching the entire given text.
"""


# Call the llm model: chat completions endpoint: import openai
def call_llm(context: str, prompt: str, api_key):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature = 0.1,
        messages=[
            {"role": "developer", "content": system_prompt},
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
    append_message_to_current_chat(prompt, full_response)

# Reasoning LLM
def call_reasoning_llm(context: str, prompt: str, api_key: str):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model = "o3-mini",
        messages=[
            {'role': 'developer', 'content': system_prompt},
            {"role": "user", "content": f"Context: {context}\nQuestion: {prompt}"}
        ],
        max_completion_tokens=64,
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
    append_message_to_current_chat(prompt, full_response)


# Search the web if the context does not contain sufficient information: import requests
# def search_web(query: str, api_key: str):
#     headers = {"Ocp-Apim-Subscription-Key": api_key}
#     search_url = "https://api.bing.microsoft.com/v7.0/search"
#     params = {"q": query, "textDecorations": True, "textFormat": "HTML"}

#     response = requests.get(search_url, headers=headers, params=params)
#     response.raise_for_status()
#     search_results = response.json()

#     if "webPages" in search_results:
#         results = search_results["webPages"]["value"]
#         answer = f"Based on the search results, here's a summary:\n\n"
#         for result in results[:5]:  # Limit to top 5 results for brevity
#             answer += f"**{result['name']}**\n{result['snippet']}\n\n"
#         return answer.strip()
#     else:
#         return "No external search results found"

def search_web(query: str):
    search_url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "key": 'AIzaSyCPuGi91baYB2dc9z2lQsSThV0RwX3iP1Y',
        "cx": '3256360bd259a492b',  
        "q": query
    }

    response = requests.get(search_url, params=params)
    response.raise_for_status()
    search_results = response.json()

    if "items" in search_results:
        results = search_results["items"]
        answer = f"Based on the search results, here's a summary:\n\n"
        for result in results[:5]:  # Limit to top 5 results for brevity
            answer += f"**{result['title']}**\n{result['snippet']}\n\n"
        return answer.strip()
    else:
        return "No external search results found"
    

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
            
            # print(f"Crawled: {url}")
            
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

# Example usage:
if __name__ == "__main__":
    site_data = crawl_website("https://example.com", max_depth=1)
    for url, content in site_data.items():
        print(f"Content from {url}:\n{content[:200]}...\n")
