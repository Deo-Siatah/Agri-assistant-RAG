from pathlib import Path

from src.loaders.pdf_loader import load_pdf


def load_all_pdfs(folder_path):

    all_docs = []

    pdf_files = Path(folder_path).glob("*.pdf")

    for pdf_file in pdf_files:

        docs = load_pdf(str(pdf_file))

        for doc in docs:

            doc.metadata["source"] = pdf_file.name

        all_docs.extend(docs)

    return all_docs