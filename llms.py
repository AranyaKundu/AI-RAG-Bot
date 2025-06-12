import streamlit as st
import requests, time, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
# LLM Import
from openai import OpenAI
from uservalidate import update_user_cost
from sentence_transformers import CrossEncoder
from langchain import PromptTemplate, LLMChain
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

    Remember: Always base your response primarily on information in the provided context, using your general knowledge only when the context is insufficient, and only mention your assumptions.
"""

system_prompt_reasoning = """
    You are an AI assistant tasked with providing detailed answers based on the given context and your general knowledge. Your goal is to analyze the context and the information provided and formulate a comprehensive, well-structured response to the question.

    context may include an uploaded file, a web search, or a website crawl. Summarize the context in a concise manner before answering the question. But do not include it in your answer.
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
    13. If there is only prompt and no uploaded file and the context is not associated with your knowledge base, answer using your general knowledge.

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
    10. No need to mention in your answer if the context doesn't matches your existing context.
    
    Remember: Always base your response primarily on information in the provided context, using your general knowledge only when the context is insufficient and only mention your assumptions.
"""

# This prompt is for the machine learning and data science llm which is not used currently.
system_prompt_analysis = """
    You are a Machine Learning Engineer and a Data Science Expert, and your primary role is to assist users in analyzing Excel spreadsheets. Your goal is to perform exploratory data analytics, predictive analytics, machine learning and quantitative data science based on the provided data.

    Core Capabilities
    1. Data Structure Understanding:
    • Recognize the layout of the Excel file, specifically focusing on:
    • Automatically identify the date range and format in Column
    • Columns: Different columns and their data types.
    • Feature and Target variables for Machine Learning.
    • Perform exploratory data analytics: Suggest code for exploratory data analytics.

    2. Exploratory Data Analysis:
    • Analyze trends and patterns based on historical data.
    • Suggest appropriate charts for different analysis types, like trends or distribution graphs.
    • Calculate key statistics such as frequency, mean, and standard deviation for specific columns.

    3. Predictive Modeling:
    • Perform Feature Engineering using different feature engineering techniques.
    • Fit machine learning models to forecast future events or occurrences based on past data.
    • Include complex ensemble and neural network models for machine learning.
    • Apply statistical methods to assess the likelihood of events happening again.
    • Recommend visualization methods to represent findings effectively.

    4. Result Interpretation:
    • Interpret results in a way that informs decision-making and provides actionable insights.
    • Provide explanations of statistical methods and analysis techniques used.

    5. Continuous Improvement and Feedback:
    • Adjust predictions and analysis methods based on user feedback and evolving data sets.
    • Encourage user engagement for more tailored and precise outputs.
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

# This Model is cuurently not used.
def machine_learning_and_data_science(context: str, prompt: str, api_key: str, temperature: 0.1):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model = "o1",
        messages=[
            {'role': 'developer', 'content': system_prompt_reasoning},
            {"role": "user", "content": f"Context: {context}\nQuestion: {prompt}"}
        ],
        max_completion_tokens=1000,
        reasoning_effort="medium",
        frequency_penalty = 1.5,
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


def search_web(query: str, num=5):
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
            "num": num
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

def crawl_website(base_url: str, max_depth: int = 2, delay: float = 0.5):
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
            response = requests.get(url, headers=headers, timeout=5)
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


def web_crawler_function(query: str, max_depth: int = 2, delay: float = 0.5, num: int = 5) -> str:
    """
    Unified web crawling tool for the agent.
    If a base_url is provided, it crawls that website and returns a summary of text content.
    Otherwise, it performs a general web search using the query.
    Returns a string summarizing the findings.
    """
    crawled_data = {}
    if query:
        url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
        urls = url_pattern.findall(query)
        if urls:
            summary = f"Crawled data from {urls}:\n\n"
            for url in urls:
                data = crawl_website(url, max_depth, delay)
                if data:
                    for url, text in data.items():
                        snippet = text[:8192].replace('\n', ' ')
                        summary += f"URL: {url}\nSnippet: {snippet}...\n\n"
                    
                else:
                    # Fallback to web search if crawling fails
                    search_results = search_web(url, num = num)
                    summary += f"Search results from fallback for {url}:\n{search_results}\n\n"
        else:
            summary = "Data from internet search" + search_web(query, num=10)
        
        return summary
    else:
        return "No search query found in prompt"

# Create cross-encoders
def rerank_cross_encoders(prompt: str, documents: list[str])-> tuple[str, list[int]]:
    if not documents:
        return "", []
    
    relevant_text = ""
    relevant_text_ids = []

    encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    ranks = encoder_model.rank(prompt, documents, top_k=3)
    for rank in ranks:
        relevant_text += documents[rank["corpus_id"]] + "\n"
        relevant_text_ids.append(rank["corpus_id"])

    return relevant_text, relevant_text_ids

# Create a context summarizer function to be used in follow up questions.
def summarize_chunk(api_key: str, turns: list[tuple[str, str]]) -> str:
    llm = OpenAI(api_key=api_key, temperature=0.1)
    template = """
        You are a concise summarizer. 
        Summarize the key facts and questions from this conversation chunk in less than 300 words.
        {turns}
    """
    turns_text = "\n".join(f"User: {u}\nAssistant: {a}" for u, a in turns)
    prompt = PromptTemplate.from_template(template)
    chain = LLMChain(llm=llm, prompt=prompt)

    return chain.run(turns=turns_text).strip()

def get_relevant_context(prompt: str, summaries: list[str], raw_turns: list[tuple[str, str]], 
                         rerank_fn, k_summaries: int = 3, k_raw_turns: int = 2) -> str:
    _, sum_ids = rerank_fn(prompt, summaries)
    chosen_summaries = [summaries[i] for i in sum_ids]

    flat_turns = [f"Q: {q}\nA: {a}" for q, a in raw_turns]
    if flat_turns:
        _, turn_ids = rerank_fn(prompt, flat_turns)
        chosen_turns = [flat_turns[i] for i in turn_ids]
    else: chosen_turns = []

    ctx = ""
    if chosen_summaries:
        ctx += "### Conversation Summaries\n" + "\n--\n".join(chosen_summaries) + "\n"
    if chosen_turns:
        ctx += "### Recent Relevant Turns\n" + "\n--\n".join(chosen_turns) + "\n"
    return ctx

