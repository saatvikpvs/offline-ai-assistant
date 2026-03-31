from crewai import Agent
from config.llm_config import get_llm

def create_conversation_agent():

    llm = get_llm()

    agent = Agent(
        role="Conversation Manager",
        goal="Understand user intent and decide which domain agent should answer",
        backstory="You coordinate the assistant and analyze user questions.",
        verbose=True,
        llm=llm
    )

    return agent