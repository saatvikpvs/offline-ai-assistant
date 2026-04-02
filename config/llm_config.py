from crewai import LLM

def get_llm():

    return LLM(
        model="ollama/npi3",
        base_url="http://localhost:11434",
        temperature=0.3,
        max_tokens=80   # limit response length
    )