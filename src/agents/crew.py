from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, WebsiteSearchTool
from src.agents.tools import search_tool, stock_price_tool
from src.agents.llm import research_llm, boss_llm

# --- TOOLS ---
# These allow  agents to research real-time market data
search_tool = SerperDevTool()
web_tool = WebsiteSearchTool()

@CrewBase
class MarketWarRoom():
    """MarketPulse CrewAI War Room for Event Analysis"""

    # Path to your YAML configurations
    agents_config = 'crew_config/agents.yaml'
    tasks_config = 'crew_config/tasks.yaml'

    # --- AGENTS (The Peers) ---

    @agent
    def macro_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['macro_strategist'],
            tools=[search_tool], # Uses the domain-restricted search
            llm=research_llm,
            verbose=True
        )

    @agent
    def quantitative_forensicist(self) -> Agent:
        return Agent(
            config=self.agents_config['quantitative_forensicist'],
            tools=[stock_price_tool], # Only needs the hard numbers
            llm=research_llm,
            verbose=True
        )

    @agent
    def sentiment_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['sentiment_architect'],
            tools=[search_tool, web_tool],
            llm=research_llm,
            verbose=True
        )

    @agent
    def sector_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['sector_specialist'],
            tools=[search_tool, web_tool],
            llm=research_llm,
            verbose=True
        )

    # --- THE INTERNAL BOSS ---

    @agent
    def chief_risk_officer(self) -> Agent:
        return Agent(
            config=self.agents_config['chief_risk_officer'],
            tools=[search_tool],
            llm=boss_llm,
            verbose=True,
            allow_delegation=True # Allows the boss to ask peers for more info
        )

    # --- TASKS (Peer-to-Boss Flow) ---

    @task
    def macro_task(self) -> Task:
        return Task(
            config=self.tasks_config['macro_analysis_task'],
            async_execution=True
        )

    @task
    def quant_task(self) -> Task:
        return Task(
            config=self.tasks_config['quantitative_audit_task'],
            async_execution=True
        )

    @task
    def sentiment_task(self) -> Task:
        return Task(
            config=self.tasks_config['sentiment_mapping_task'],
            async_execution=True
        )

    @task
    def sector_task(self) -> Task:
        return Task(
            config=self.tasks_config['industry_impact_task'],
            async_execution=True
        )

    @task
    def final_decision_task(self) -> Task:
        """
        This is the synthesis task. It takes the output of the 4 peers 
        as context and produces the final investment thesis.
        """
        return Task(
            config=self.tasks_config['final_risk_verdict_task'],
            context=[
                self.macro_task(), 
                self.quant_task(), 
                self.sentiment_task(), 
                self.sector_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the MarketPulse War Room crew"""
        return Crew(
            agents=self.agents, # Automatically pulls all @agent functions
            tasks=self.tasks,   # Automatically pulls all @task functions
            process=Process.sequential, # The 'context' handles the peer logic -> don't allow the boss to skip agents/tasks
            # Max 5 requests per minute to stay safe on lower API tiers
            max_rpm=5,
            verbose=True
        )
    
"""
# Inside LangGraph node or FastAPI endpoint
async def run_analysis(event_data):
    war_room = MarketWarRoom().crew()
    
    # Use kickoff_async to not block the event loop
    result = await war_room.kickoff_async(inputs={'event': event_data})
    
    return result
"""