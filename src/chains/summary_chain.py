from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.chains.prompt_loader import load_prompt

def build_summary_chain(llm):
    template = load_prompt(
        "src/prompts/summary_prompt.yaml"
    )

    prompt = PromptTemplate(
        template = template,
        input_variables=["context"]
    )

    return prompt | llm | StrOutputParser()