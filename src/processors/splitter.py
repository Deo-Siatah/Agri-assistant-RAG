from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config.config_loader import load_config


def split_documents(documents):
    config = load_config()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["splitting"]["chunk_size"],
        chunk_overlap=config["splitting"]["chunk_overlap"]
    )

    return splitter.split_documents(documents)