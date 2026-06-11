from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.config_loader import load_config

def get_llm():
    config = load_config()

    return ChatGoogleGenerativeAI(
        model=config["llm"]["model"],
        temperature=config["llm"]["temperature"]
        )