from langchain_groq import ChatGroq
from src.config.app_config import get_app_config
from src.config.settings import get_settings

def get_llm():
    settings = get_settings()
    config = get_app_config()

    return ChatGroq(
        model=config.llm.model,
        temperature=config.llm.temperature,
        api_key=settings.groq_api_key
        )