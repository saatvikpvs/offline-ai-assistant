from crewai import LLM

def get_llm():
    llm = LLM(
        model="ollama/llama3",
        base_url="http://localhost:11434"
    )
    return llm