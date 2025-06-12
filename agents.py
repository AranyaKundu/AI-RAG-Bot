from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import FileWriterTool, DirectoryReadTool
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from llms import web_crawler_function
from system_prompts import (
    coding_helper, qa_engineer, software_product_manager, 
    nuclear_scientist, nuclear_content_collector, 
    energy_market_data_collector, energy_market_analyst, energy_content_writer,
    generic_agent_prompt, project_manager
)
from openai import OpenAI
import os
import streamlit as st

# Set OpenAI API key as environment variable for crewAI
os.environ["OPENAI_API_KEY"] = st.secrets["api_keys"]["openai"]
OPENAI_API_KEY = st.secrets["api_keys"]["openai"]
client = OpenAI(api_key=OPENAI_API_KEY)

# Create a tool for webcrawling
class WebCrawlerInput(BaseModel):
    query: str = Field(description="The search query or selection of starting urls")
    max_depth: int = Field(2, description="Max-depth for crawling websites")
    delay: float = Field(0.5, description="Delay between requests in seconds")
    num: int = Field(5, description="Number of results or pages to crawl")


class WebCrawlerTool(BaseTool):
    name: str = "web_crawler_tool"
    description: str = "A tool for searching or scraping information from the internet"
    args_schema: Type[BaseModel] = WebCrawlerInput

    def _run(self, query: str, max_depth: int = 2, delay: float = 0.5, num: int = 5) -> str:
        return web_crawler_function(query=query, max_depth=max_depth, delay=delay, num=num)

# Some specified agents
def software_development(query, model, temperature, max_tokens):
     # Manager agent
    manager_role, manager_goal, manager_backstory = software_product_manager()
    manager = Agent(
        role=str(manager_role),
        goal=str(manager_goal),
        backstory=manager_backstory,
        allow_delegation=True,
    )
    # Programming helper
    coder_role, coder_goal, coder_backstory, coder_task_description = coding_helper(query)
    programmer = Agent(
        role=str(coder_role),
        goal=str(coder_goal),
        backstory=str(coder_backstory),
        llm=LLM(
            model = model,
            temperature = temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY
        ),
        tools=[DirectoryReadTool()],
        allow_delegation = False,
        verbose= True,
        max_iter=10,
        code_execution_mode="safe", 
        max_execution_time=120,  
        max_retry_limit=3 
    )

    programming_task = Task(
        description=coder_task_description,
        agent = programmer,
        expected_output=f"""A code that solves the user query. The code should be well-structured, 
        efficient, and follow best practices. 
        """,
        tools=[DirectoryReadTool()]
    )

    tester_role, tester_goal, tester_backstory, tester_task_description = qa_engineer()
    tester = Agent(
        role=str(tester_role),
        goal=str(tester_goal),
        backstory=str(tester_backstory),
        llm=LLM(
            model = model,
            temperature = temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY
        ),
        tools=[DirectoryReadTool()],
        allow_delegation = False,
        verbose= True
    )

    testing_task = Task(
        description=tester_task_description,
        agent=tester,
        expected_output=f"""
            A clear, concise description of the bugs in the features based on the code by the programmer agent. 
            Provide the entire code from the programmer to the response chat if no bug is found. Write the code
            and create and save it to the folder "./output_code/" with the name "response.py".
        """,
        tools=[DirectoryReadTool(), FileWriterTool()]
    )
    
    crew_programmer = Crew(
        agents = [programmer, tester],
        tasks=[programming_task, testing_task],
        process=Process.sequential,
        verbose=True,
        # manager_agent=manager
    )
    return crew_programmer


def Nuclear_research(query, model, temperature, max_tokens):
    nuclear_scientist_role, nuclear_scientist_goal, nuclear_scientist_backstory, nuclear_scientist_task_description = nuclear_scientist(query)
    nuclear_science_agent = Agent(
        role=str(nuclear_scientist_role),
        goal=str(nuclear_scientist_goal),
        backstory=str(nuclear_scientist_backstory),
        llm=LLM(
            model = model,
            temperature = temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY
        ),
        allow_delegation = False,
        verbose= True
    )

    nuclear_science_agent_task = Task(
        description=nuclear_scientist_task_description,
        agent=nuclear_science_agent,
        expected_output=f"A clear and concise answer to the user query."
    )

    nuclear_agent_role, nuclear_agent_goal, nuclear_agent_backstory, nuclear_agent_task_description = nuclear_content_collector(query)
    nuclear_content_collector_agent = Agent(
        role=str(nuclear_agent_role),
        goal=str(nuclear_agent_goal),
        backstory=str(nuclear_agent_backstory),
        llm=LLM(
            model = model,
            temperature = temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY
        ),
        allow_delegation = False,
        verbose= True
    )
    nuclear_content_collector_task = Task(
        description=nuclear_agent_task_description,
        agent=nuclear_content_collector_agent,
        expected_output=f"A concise summary of the data collected from the internet based on the query."
    )

    crew_nuclear_researcher = Crew(
        agents=[nuclear_content_collector_agent, nuclear_science_agent],
        tasks=[nuclear_content_collector_task, nuclear_science_agent_task],
        process=Process.sequential,
        verbose=True
    )

    return crew_nuclear_researcher

# Energy Analytics Agent
def Energy_market_research(query, model, temperature, max_tokens):
    energy_agent_role, energy_agent_goal, energy_agent_backstory, energy_agent_task_description = energy_market_data_collector(query)
    energy_data_engineer = Agent(
        role=str(energy_agent_role),
        goal=str(energy_agent_goal),
        backstory=str(energy_agent_backstory),
        llm=LLM(
            model = model,
            temperature = temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY
        ),
        allow_delegation = False,
        verbose= True,
        tools=[WebCrawlerTool()]
    )
    energy_data_engineer_task = Task(
        description=energy_agent_task_description,
        agent=energy_data_engineer,
        expected_output=f"A concise report that can be used by the Energy Market Analyst as a knowledge base to provide analytical insights.",
        tools=[WebCrawlerTool()]
    )
    energy_analyst_role, energy_analyst_goal, energy_analyst_backstory, energy_analyst_task_description = energy_market_analyst()
    energy_analyst_agent = Agent(
        role=str(energy_analyst_role),
        goal=str(energy_analyst_goal),
        backstory=str(energy_analyst_backstory),
        llm=LLM(
            model = model,
            temperature = temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY
        ),
        allow_delegation = False,
        verbose= True
    )

    energy_analyst_agent_task = Task(
        description=energy_analyst_task_description,
        agent = energy_analyst_agent,
        expected_output=f"""A concise report of the analysis of Energy Data that can be utilized by the Energy Content Writer Agent to 
        create a business report. Make the Analysis lengthy enough that it can be created into a 5000 word business report. So make sure 
        to do a detailed analysis insted of a summaru of bullet points."""
    )

    energy_content_writer_role, energy_content_writer_goal, energy_content_writer_backstory, energy_content_writer_task_description = energy_content_writer()
    energy_content_writer_agent = Agent(
        role=str(energy_content_writer_role),
        goal=str(energy_content_writer_goal),
        backstory=str(energy_content_writer_backstory),
        llm=LLM(
            model = model,
            temperature = temperature,
            max_tokens=max_tokens,
            api_key=OPENAI_API_KEY
        ),
        allow_delegation = False,
        verbose= True
    )
    energy_content_writer_task = Task(
        description=energy_content_writer_task_description,
        agent=energy_content_writer_agent,
        expected_output=f"""A business report on the energy market based on the analysis done by the energy market analyst in about 5000 words. 
        Make it lengthy and informative enough, so that it reaches 5000 words or more. Keep the analysis in detail."""
    )

    crew_energy_markets = Crew(
        agents=[energy_data_engineer, energy_analyst_agent, energy_content_writer_agent],
        tasks=[energy_data_engineer_task, energy_analyst_agent_task, energy_content_writer_task],
        process=Process.sequential,
        verbose=True
    )
    return crew_energy_markets




# Need to complete the code for a generic agent
# Generic Multi-agent idea: The user will be defining their own agents and the agent parameters
# The users will choose the number of agents for any task between 1 & 5 agents (This is important)
# Generic Agents should be called based on the count selected.
# The users will choose the process (sequential or hierarchical)

def generic_agent_Setup(query, model, temperature, max_tokens, manager="Yes", agents_count=3):
    """
        Creates an agent based on the properties set by the user
    """
    # Define an agent: Agents will be multiplied based on instructions by the user.
    # Agent General Settings:

    manager_role, manager_goal, manager_backstory = project_manager()
    manager_agent = Agent(
        role=str(manager_role),
        goal=str(manager_goal),
        backstory=str(manager_backstory),
        allow_delegation=True,
    )

    # Create multiple agents based on agents_count
    agents_list = []
    tasks_list = []
    
    for i in range(agents_count):
        agent_role, agent_goal, agent_backstory, agent_task_description = generic_agent_prompt(query)
        # Customize each agent slightly to ensure they have different perspectives
        agent_role = f"{agent_role} #{i+1}"
        agent_goal = f"{agent_goal} with focus on aspect #{i+1}"
        
        agent_props = Agent(
            role=str(agent_role),
            goal=str(agent_goal),
            backstory=str(agent_backstory),
            llm=LLM(
                model = model,
                temperature = temperature,
                max_tokens=max_tokens,
                api_key=OPENAI_API_KEY
            ),
            allow_delegation = False,
            verbose= True,
            max_iter=10,
            tools = [FileWriterTool(), DirectoryReadTool()]
        )
        
        agent_task = Task(
            description=f"{agent_task_description} (Agent #{i+1})",
            agent=agent_props,
            tools=[WebCrawlerTool(), DirectoryReadTool(), FileWriterTool()],
            expected_output=f"""A clear and concise answer to the user query, if you are the final agent in the chain. Else create
            a summary that can be used as a knowledge base for other agents in the chain."""
        )
        
        agents_list.append(agent_props)
        tasks_list.append(agent_task)

    # Create crew with appropriate process
    crew_defn = Crew(
        agents=agents_list,
        tasks=tasks_list,
        process=Process.hierarchical if manager == "Yes" else Process.sequential,
        manager_agent = manager_agent if manager == "Yes" else None,
        verbose=True
    )
    
    return crew_defn


