from crewai import Agent
from config.llm_config import get_llm

def create_governance_agent():

    llm = get_llm()

    agent = Agent(
        role="Government Assistant",
        goal="Explain government schemes and policies",
        backstory="You help citizens understand public services.",
        verbose=True,
        llm=llm
    )

    return agent