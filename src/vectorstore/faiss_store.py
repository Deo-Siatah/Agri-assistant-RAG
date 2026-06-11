from pathlib import Path

from langchain_community.vectorstores import FAISS

from src.config.config_loader import load_config


def create_faiss_store(chunks, embeddings):

    config = load_config()

    vector_path = config["vectorstore"]["path"]
    rebuild = config["vectorstore"]["rebuild"]

    if Path(vector_path).exists() and not rebuild:

        print("Loading existing vector store...")

        return FAISS.load_local(
            vector_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

    print("Building new vector store...")

    vector_store = FAISS.from_documents(
        chunks,
        embeddings
    )

    vector_store.save_local(
        vector_path
    )

    print("Vector store saved.")

    return vector_store