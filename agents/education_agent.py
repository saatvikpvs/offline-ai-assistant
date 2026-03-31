from crewai import Agent
from config.llm_config import get_llm

def create_education_agent():

    llm = get_llm()

    agent = Agent(
        role="Education Expert",
        goal="Explain educational concepts clearly",
        backstory="You are a tutor who explains science and mathematics topics.",
        verbose=True,
        llm=llm
    )

    return agent