from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.chains.prompt_loader import load_prompt_config


def build_csv_analysis_chain(llm):
    prompt_config = load_prompt_config("src/prompts/csv_analysis.yaml")
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_config["system"]),
        ("human", prompt_config["template"])
    ])
    return prompt | llm 