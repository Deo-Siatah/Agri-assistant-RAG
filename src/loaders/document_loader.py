import logging
from pathlib import Path

from src.loaders.pdf_loader import load_pdf

# Configure logging to output warnings and errors to your console
logger = logging.getLogger(__name__)


def load_all_pdfs(folder_path):
    all_docs = []
    pdf_files = Path(folder_path).glob("*.pdf")

    for pdf_file in pdf_files:
        try:
            # Attempt to parse the PDF
            docs = load_pdf(str(pdf_file))

            for doc in docs:
                doc.metadata["source"] = pdf_file.name

            all_docs.extend(docs)
            logger.info(f"Successfully loaded: {pdf_file.name}")

        except Exception as e:
            # Catch memory errors, corruption, and parsing failures
            logger.warning(
                f"Skipping corrupt or unreadable PDF '{pdf_file.name}': {e}"
            )

    return all_docs