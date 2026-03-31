from crewai import Agent
from config.llm_config import get_llm
from memory.memory_store import MemoryStore

memory_store = MemoryStore()

def create_memory_agent():

    llm = get_llm()

    agent = Agent(
        role="Memory Manager",
        goal="Store and retrieve conversation context",
        backstory="You remember user information and previous conversations.",
        verbose=True,
        llm=llm
    )

    return agent