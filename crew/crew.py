from crewai import Crew, Task

from agents.conversation_agent import create_conversation_agent
from agents.education_agent import create_education_agent
from agents.medical_agent import create_medical_agent
from agents.governance_agent import create_governance_agent


def run_crew(user_input):

    conversation_agent = create_conversation_agent()
    education_agent = create_education_agent()
    medical_agent = create_medical_agent()
    governance_agent = create_governance_agent()

    # Step 1: Conversation agent decides topic
    topic = conversation_agent.llm.call(user_input).lower()

    # Step 2: Select correct agent
    if "education" in topic:
        selected_agent = education_agent
    elif "medical" in topic:
        selected_agent = medical_agent
    elif "governance" in topic:
        selected_agent = governance_agent
    else:
        selected_agent = conversation_agent

    # Step 3: Create ONE task
    task = Task(
        description=f"Answer the user query: {user_input}",
        agent=selected_agent,
        expected_output="Provide a helpful response"
    )

    # Step 4: Run crew with only that agent
    crew = Crew(
        agents=[selected_agent],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()

    return result