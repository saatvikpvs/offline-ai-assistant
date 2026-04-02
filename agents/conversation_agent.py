from crewai import Agent
from config.llm_config import get_llm


def create_conversation_agent():

    llm = get_llm()

    agent = Agent(
        role="Conversation Manager",
        goal="Understand the user's query and decide which agent should handle it",
        backstory=(
            "You are the main controller of an offline AI assistant. "
            "Your job is to read the user's query and classify it into one of these topics:\n"
            "1. education\n"
            "2. medical\n"
            "3. governance\n"
            "4. general\n\n"
            "If it is a greeting or normal conversation like 'hi', 'hello', 'who are you', "
            "classify it as 'general'.\n"
            "Return ONLY one word from these: education, medical, governance, general."
        ),
        verbose=True,
        llm=llm
    )

    return agent