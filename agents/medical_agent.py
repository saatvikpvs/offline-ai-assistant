from crewai import Agent
from config.llm_config import get_llm

def create_medical_agent():

    llm = get_llm()

    agent = Agent(
        role="Medical Advisor",
        goal="Provide general health information",
        backstory="You provide health guidance but avoid diagnosing diseases.",
        verbose=True,
        llm=llm
    )

    return agent