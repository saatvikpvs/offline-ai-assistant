from crewai import Crew, Task

from agents.conversation_agent import create_conversation_agent
from agents.memory_agent import create_memory_agent
from agents.knowledge_agent import create_knowledge_agent
from agents.action_agent import create_action_agent
from agents.education_agent import create_education_agent
from agents.medical_agent import create_medical_agent
from agents.governance_agent import create_governance_agent


def run_crew(user_input):

    conversation_agent = create_conversation_agent()
    memory_agent = create_memory_agent()
    knowledge_agent = create_knowledge_agent()
    action_agent = create_action_agent()

    education_agent = create_education_agent()
    medical_agent = create_medical_agent()
    governance_agent = create_governance_agent()

    conversation_task = Task(
        description=f"Analyze the user query and determine the topic: {user_input}",
        agent=conversation_agent,
        expected_output="Identify if the query is education, medical, or governance."
    )

    knowledge_task = Task(
        description="Retrieve relevant information from the local knowledge base.",
        agent=knowledge_agent,
        expected_output="Provide relevant factual information."
    )

    education_task = Task(
        description=f"Answer the question for educational context: {user_input}",
        agent=education_agent,
        expected_output="Clear explanation for the user."
    )

    medical_task = Task(
        description=f"Provide medical information for: {user_input}",
        agent=medical_agent,
        expected_output="General health guidance."
    )

    governance_task = Task(
        description=f"Provide governance related information for: {user_input}",
        agent=governance_agent,
        expected_output="Information about government policies or schemes."
    )

    memory_task = Task(
        description="Store this conversation in memory.",
        agent=memory_agent,
        expected_output="Conversation stored successfully."
    )

    action_task = Task(
        description="Execute any required system actions.",
        agent=action_agent,
        expected_output="Action completed if required."
    )

    crew = Crew(
        agents=[
            conversation_agent,
            memory_agent,
            knowledge_agent,
            action_agent,
            education_agent,
            medical_agent,
            governance_agent
        ],
        tasks=[
            conversation_task,
            knowledge_task,
            education_task,
            medical_task,
            governance_task,
            memory_task,
            action_task
        ],
        verbose=True
    )

    result = crew.kickoff()

    return result