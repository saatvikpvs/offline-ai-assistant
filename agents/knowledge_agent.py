from crewai import Agent
from config.llm_config import get_llm
from knowledge.knowledge_base import KnowledgeBase

kb = KnowledgeBase()

def create_knowledge_agent():

    llm = get_llm()

    agent = Agent(
        role="Knowledge Retriever",
        goal="Retrieve relevant information from the local knowledge base",
        backstory="You search stored knowledge and return relevant context.",
        verbose=True,
        llm=llm
    )

    return agent