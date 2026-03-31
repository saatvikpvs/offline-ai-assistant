from agents.conversation_agent import create_conversation_agent
from agents.education_agent import create_education_agent
from agents.medical_agent import create_medical_agent
from agents.governance_agent import create_governance_agent
from crew.crew import run_crew
from utils.router import route_query
from utils.language_handler import detect_language, translate_to_english, translate_from_english

from interface.speech_input import get_user_input
from interface.speech_output import speak

def main():

    conversation_agent = create_conversation_agent()
    education_agent = create_education_agent()
    medical_agent = create_medical_agent()
    governance_agent = create_governance_agent()

    print("Offline AI Assistant Ready")

    while True:

        user_input = get_user_input()

        lang = detect_language(user_input)

        english_input = translate_to_english(user_input)

        agent_type = route_query(english_input)

        response = run_crew(english_input)
        final_response = translate_from_english(response, lang)

        speak(final_response)


if __name__ == "__main__":
    main()