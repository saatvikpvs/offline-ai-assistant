from crewai import Agent
from config.llm_config import get_llm


def create_conversation_agent():

    llm = get_llm()

    agent = Agent(
        role="Master Conversation Router & Classifier",
        goal="Accurately analyze the user's intent and route their query to the single most appropriate specialized department.",
        backstory=(
            "You are the central brain and routing controller of an advanced offline AI assistant. "
            "Your sole purpose is to read the user's query and classify it strictly into one of the following domains:\n"
            "1. 'education' - for all questions regarding science, math, learning, or academic concepts.\n"
            "2. 'medical' - for questions regarding health, wellness, symptoms, or biology.\n"
            "3. 'governance' - for queries regarding public policies, laws, schemes, or citizen services.\n"
            "4. 'general' - for conversational greetings (like 'hi', 'hello', 'who are you'), or anything else that doesn't fit the above.\n\n"
            "CRITICAL: You must output ONLY ONE WORD from the list above. No punctuation, no extra text, no explanations."
        ),
        verbose=True,
        llm=llm
    )

    return agent