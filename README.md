# Agri Assistant

Agri Assistant is a Python-based agricultural question-answering tool that combines document retrieval, CSV analysis, and weather analysis in one CLI workflow.

It loads PDF documents from `data/pdfs`, splits them into chunks, builds a FAISS vector store, and uses a Google Gemini model through LangChain to answer questions, summarize documents, and route requests to the right tool.

## What This Project Does

- Answers questions from indexed PDF content using retrieval-augmented generation.
- Summarizes the loaded document corpus.
- Analyzes the agricultural CSV dataset in `data/csv/farm_production.csv`.
- Fetches live weather data through the Open-Meteo API and generates agricultural weather guidance.
- Logs interactions and confidence signals for traceability.

## What Was Achieved

- Built a working CLI entrypoint in `main.py` for interactive use.
- Added document loading, chunking, embedding, and FAISS-based retrieval.
- Added a router that directs queries to PDF, CSV, or weather workflows.
- Added dedicated chains for QA, summarization, CSV analysis, and weather analysis.
- Added logging and confidence classification for responses.
- Organized the codebase into clear modules under `src/` for loaders, chains, tools, retrieval, embeddings, prompts, and configuration.

## Project Structure

- `main.py` - interactive CLI entrypoint
- `src/agents` - query routing logic
- `src/chains` - LangChain workflows for QA, summary, CSV, and weather analysis
- `src/config` - application and runtime settings
- `src/loaders` - PDF and CSV loading helpers
- `src/processors` - document splitting utilities
- `src/retrieval` - vector retrieval helpers
- `src/tools` - CSV and weather tools
- `src/vectorstore` - FAISS store creation
- `data/pdfs` - source PDF documents
- `data/csv` - dataset inputs
- `data/vectorstore` - persisted vector store artifacts

## Requirements

- Python 3.12 or newer
- A working internet connection for Google Gemini and Open-Meteo requests
- A `.env` file with your Google API key

## Setup

1. Create and activate a virtual environment.

	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

2. Install the project dependencies.

	```powershell
	pip install faiss-cpu langchain langchain-community langchain-google-genai langchain-huggingface pandas pydantic pypdf python-dotenv pyyaml requests rich sentence-transformers
	```

3. Create a `.env` file in the project root and add your Google API key.

	```env
	GOOGLE_API_KEY=your_google_api_key_here
	```

4. Add the source PDFs you want to index to `data/pdfs`.

5. Make sure the CSV dataset exists at `data/csv/farm_production.csv`.

## Run The App

Start the CLI with:

```powershell
python main.py
```

When the app starts, you can:

- Ask a question
- Generate a summary of the loaded PDF context
- Exit the program

Depending on the query, the router will send the request to the PDF retrieval workflow, the CSV analytics workflow, or the weather workflow.

## Notes

- The vector store is stored under `data/vectorstore`.
- The app currently rebuilds the FAISS store from the loaded documents at startup.
- Weather analysis uses the Open-Meteo API and does not require a separate weather key.

## Author

Created personally by Deo-Siatah as the sole contributor to this project.
