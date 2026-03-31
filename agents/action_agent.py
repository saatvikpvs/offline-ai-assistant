from crewai import Agent
from config.llm_config import get_llm

def create_action_agent():

    llm = get_llm()

    agent = Agent(
        role="Action Executor",
        goal="Perform system actions like opening apps or controlling avatar",
        backstory="You execute commands requested by the user.",
        verbose=True,
        llm=llm
    )

    return agent