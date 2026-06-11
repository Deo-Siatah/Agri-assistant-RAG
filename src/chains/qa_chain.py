from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.chains.prompt_loader import load_prompt

def build_qa_chain(llm):
    template = load_prompt("src/prompts/qa_prompt.yaml")
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    return prompt | llm | StrOutputParser()