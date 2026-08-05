# Agri Assistant Codebase Summary

## 1. Directory / File Tree

| Path | Purpose |
| --- | --- |
| [main.py](main.py) | CLI entry point that loads PDFs, builds embeddings and FAISS, creates chains and tools, routes questions, and prints answers. |
| [pyproject.toml](pyproject.toml) | Project metadata and runtime dependency list. |
| [README.md](README.md) | High-level project overview, setup notes, and run instructions. |
| [structure](structure) | Stale tree sketch from an earlier version of the repo; it no longer matches the current layout. |
| [test.py](test.py) | Manual Open-Meteo smoke script, not an automated test suite. |
| [.env](.env) | Local environment file loaded at startup by dotenv. |
| [.gitignore](.gitignore) | Ignore rules for local and generated artifacts. |
| [.python-version](.python-version) | Python version pin for the workspace. |
| [uv.lock](uv.lock) | Dependency lockfile. |
| [data/csv/farm_production.csv](data/csv/farm_production.csv) | Primary CSV dataset consumed by the CSV tool. |
| [data/csv/data_season.csv](data/csv/data_season.csv) | Secondary CSV dataset present in the repo but not referenced by the main flow. |
| [data/outputs/rag_logs.json](data/outputs/rag_logs.json) | Append-only JSONL interaction log for CSV and PDF answer paths. |
| [data/pdfs/2546-Article Text-7158-3-10-20241227 (2).pdf](data/pdfs/2546-Article%20Text-7158-3-10-20241227%20(2).pdf) | Source PDF document used for retrieval. |
| [data/pdfs/Determinants_of_Maize_Production_and_Its_Supply_Re.pdf](data/pdfs/Determinants_of_Maize_Production_and_Its_Supply_Re.pdf) | Source PDF document used for retrieval. |
| [data/pdfs/Market-report-Maize-Kenya-1.pdf](data/pdfs/Market-report-Maize-Kenya-1.pdf) | Source PDF document used for retrieval. |
| [data/pdfs/Planting_strategies_of_maize_farmers_in_Kenya_A_si.pdf](data/pdfs/Planting_strategies_of_maize_farmers_in_Kenya_A_si.pdf) | Source PDF document used for retrieval. |
| [data/vectorstore/index.faiss](data/vectorstore/index.faiss) | Persisted FAISS index. |
| [data/vectorstore/index.pkl](data/vectorstore/index.pkl) | Persisted FAISS metadata/docstore artifact. |
| [src/agents/router.py](src/agents/router.py) | Keyword router that chooses PDF, CSV, or weather handling. |
| [src/chains/llm.py](src/chains/llm.py) | Gemini model factory. |
| [src/chains/prompt_loader.py](src/chains/prompt_loader.py) | YAML prompt loader helpers. |
| [src/chains/qa_chain.py](src/chains/qa_chain.py) | PDF question-answering chain. |
| [src/chains/summary_chain.py](src/chains/summary_chain.py) | PDF summarization chain. |
| [src/chains/csv_analysis_chain.py](src/chains/csv_analysis_chain.py) | Natural-language explanation chain for CSV statistics. |
| [src/chains/weather_analysis_chain.py](src/chains/weather_analysis_chain.py) | Natural-language explanation chain for weather data. |
| [src/config/app.yaml](src/config/app.yaml) | Central app configuration for model, retrieval, splitting, vector store, and logging. |
| [src/config/config_loader.py](src/config/config_loader.py) | YAML config loader. |
| [src/config/settings.py](src/config/settings.py) | Dotenv bootstrap that loads environment variables on import. |
| [src/embeddings/embedding_service.py](src/embeddings/embedding_service.py) | Hugging Face embedding factory. |
| [src/evaluation/confidence.py](src/evaluation/confidence.py) | Score-to-confidence classifier. |
| [src/evaluation/logger.py](src/evaluation/logger.py) | JSONL interaction logger. |
| [src/loaders/csv_loader.py](src/loaders/csv_loader.py) | Pandas CSV loader helper. |
| [src/loaders/document_loader.py](src/loaders/document_loader.py) | Loads all top-level PDFs and annotates source metadata. |
| [src/loaders/pdf_loader.py](src/loaders/pdf_loader.py) | Wrapper around LangChain PyPDFLoader. |
| [src/parsers/qa_response.py](src/parsers/qa_response.py) | Pydantic schema for QA responses; currently unused by the main flow. |
| [src/processors/splitter.py](src/processors/splitter.py) | Recursive text splitter for PDF chunks. |
| [src/prompts/csv_analysis.yaml](src/prompts/csv_analysis.yaml) | Prompt template for CSV interpretation. |
| [src/prompts/qa_prompt.yaml](src/prompts/qa_prompt.yaml) | Prompt template for PDF QA. |
| [src/prompts/summary_prompt.yaml](src/prompts/summary_prompt.yaml) | Prompt template for PDF summarization. |
| [src/prompts/weather_analysis.yaml](src/prompts/weather_analysis.yaml) | Prompt template for weather interpretation. |
| [src/retrieval/retrieval_service.py](src/retrieval/retrieval_service.py) | Similarity search helper with score filtering. |
| [src/retrieval/retriever.py](src/retrieval/retriever.py) | Retriever wrapper that is not used by main.py. |
| [src/services/weather_service.py](src/services/weather_service.py) | Open-Meteo HTTP client. |
| [src/tools/csv_tool.py](src/tools/csv_tool.py) | Rule-based analytics over the farm production dataset. |
| [src/tools/pdf_tool.py](src/tools/pdf_tool.py) | Empty placeholder file. |
| [src/tools/weather_tool.py](src/tools/weather_tool.py) | Normalizes Open-Meteo current weather data into a compact dict. |
| [src/vectorstore/faiss_store.py](src/vectorstore/faiss_store.py) | Builds or reloads the FAISS vector store. |
| [src/memory/](src/memory/) | Empty directory. |
| [tests/](tests/) | Empty test directory. |

## 2. Architecture Overview

The application is a single-process CLI workflow. Startup begins in [main.py](main.py), which imports settings, loads all PDFs from [data/pdfs](data/pdfs), splits them into chunks, embeds the chunks, and builds or reloads the FAISS store under [data/vectorstore](data/vectorstore). The model comes from [src/chains/llm.py](src/chains/llm.py), which creates a Gemini chat model from [src/config/app.yaml](src/config/app.yaml).

At runtime, the menu in [main.py](main.py) has three paths. The summary path concatenates all loaded PDF chunk text and passes the first 15000 characters to the summary chain. The question-answering path first calls the router in [src/agents/router.py](src/agents/router.py) to choose CSV, weather, or PDF. CSV requests are evaluated by the CSV tool and then explained by the CSV analysis chain. Weather requests are evaluated by the weather tool and then explained by the weather analysis chain. PDF requests run similarity search against FAISS, filter by score threshold, build context from the retrieved chunks, and send that context into the QA chain. Output is printed to the console, and CSV plus PDF paths append interaction records to [data/outputs/rag_logs.json](data/outputs/rag_logs.json).

The PDF path is the only retrieval-augmented path. It uses [src/loaders/document_loader.py](src/loaders/document_loader.py) to load documents, [src/processors/splitter.py](src/processors/splitter.py) to chunk them, [src/embeddings/embedding_service.py](src/embeddings/embedding_service.py) to create embeddings, [src/vectorstore/faiss_store.py](src/vectorstore/faiss_store.py) to create the vector store, and [src/retrieval/retrieval_service.py](src/retrieval/retrieval_service.py) to fetch the final context. [src/retrieval/retriever.py](src/retrieval/retriever.py) exists as an alternate retriever builder, but the current CLI does not use it.

## 3. LLM and Chain Components

| Component | Model or Parser | Prompt Structure | Retrieval or Inputs | Notes |
| --- | --- | --- | --- | --- |
| [src/chains/llm.py](src/chains/llm.py) | ChatGoogleGenerativeAI with gemini-2.5-flash-lite at temperature 0.2 | No prompt; this is the model factory. | Uses values from [src/config/app.yaml](src/config/app.yaml). | All chains depend on this shared model constructor. |
| [src/chains/qa_chain.py](src/chains/qa_chain.py) | PromptTemplate + StrOutputParser | Single template loaded from [src/prompts/qa_prompt.yaml](src/prompts/qa_prompt.yaml). The prompt instructs the model to answer only from the supplied context and to say it could not find the answer if needed. | Context is built in [main.py](main.py) from retrieved PDF chunks. | Output is a plain string. |
| [src/chains/summary_chain.py](src/chains/summary_chain.py) | PromptTemplate + StrOutputParser | Single template loaded from [src/prompts/summary_prompt.yaml](src/prompts/summary_prompt.yaml). It asks for main findings, recommendations, and agricultural insights. | Context is the concatenated PDF text passed from [main.py](main.py). | The main flow truncates input context to 15000 characters before invocation. |
| [src/chains/csv_analysis_chain.py](src/chains/csv_analysis_chain.py) | ChatPromptTemplate; no output parser attached | System and human messages are loaded from [src/prompts/csv_analysis.yaml](src/prompts/csv_analysis.yaml). The system prompt asks for concise explanation, no invented numbers, and agricultural implications. | Inputs are the user question and the CSV statistic returned by [src/tools/csv_tool.py](src/tools/csv_tool.py). | The chain returns the raw chat message; [main.py](main.py) reads .content. |
| [src/chains/weather_analysis_chain.py](src/chains/weather_analysis_chain.py) | ChatPromptTemplate + StrOutputParser | System and human messages are loaded from [src/prompts/weather_analysis.yaml](src/prompts/weather_analysis.yaml). The system prompt frames the model as an agricultural weather advisor. | Inputs are the user question and the dict returned by [src/tools/weather_tool.py](src/tools/weather_tool.py). | Output is a plain string. |
| PDF retrieval stack | FAISS + Hugging Face embeddings | Not a chain prompt; this is the retrieval layer for QA. | PDFs are loaded by [src/loaders/document_loader.py](src/loaders/document_loader.py), chunked by [src/processors/splitter.py](src/processors/splitter.py), embedded by [src/embeddings/embedding_service.py](src/embeddings/embedding_service.py), stored in [src/vectorstore/faiss_store.py](src/vectorstore/faiss_store.py), and queried by [src/retrieval/retrieval_service.py](src/retrieval/retrieval_service.py). | Retrieval uses similarity_search_with_score and a threshold filter from config. |

Prompt details:

| Prompt File | Structure | Purpose |
| --- | --- | --- |
| [src/prompts/qa_prompt.yaml](src/prompts/qa_prompt.yaml) | Single template string | PDF QA with context grounding and a fixed fallback sentence. |
| [src/prompts/summary_prompt.yaml](src/prompts/summary_prompt.yaml) | Single template string | Summarize the loaded document corpus. |
| [src/prompts/csv_analysis.yaml](src/prompts/csv_analysis.yaml) | System message plus human template | Turn CSV statistics into short agricultural explanations. |
| [src/prompts/weather_analysis.yaml](src/prompts/weather_analysis.yaml) | System message plus human template | Turn weather observations into agricultural advice. |

## 4. Tool Definitions and Routing

| Route or Tool | Inputs | Outputs | Behavior |
| --- | --- | --- | --- |
| [src/agents/router.py](src/agents/router.py) | A user question string | One of csv, weather, or pdf | Lowercases the question and checks keyword lists. CSV keywords are checked first, then weather keywords. If neither matches, the fallback is pdf. Because rainfall appears in both lists, CSV wins for overlapping rainfall queries. |
| [src/tools/csv_tool.py](src/tools/csv_tool.py) | CSV path at construction time; question string at run time | Mixed outputs: dicts for some metrics, strings for others | Loads [data/csv/farm_production.csv](data/csv/farm_production.csv) into pandas and answers only when the query contains exact phrases such as average yield, total yield, highest yield, lowest yield, top counties, best crop, rainfall relationship, or average rainfall. Otherwise it returns a refusal string. |
| [src/tools/weather_tool.py](src/tools/weather_tool.py) | Latitude and longitude | A compact dict with temperature, humidity, weather_code, precipitation, and wind_speed | Calls [src/services/weather_service.py](src/services/weather_service.py), extracts the current weather block, and normalizes the response for the chain. |
| PDF retrieval path | User question string | Retrieved document chunks plus similarity scores | This is the fallback route rather than a dedicated tool class. [main.py](main.py) uses the retrieved PDF chunks as context for the QA chain. |
| [src/tools/pdf_tool.py](src/tools/pdf_tool.py) | None | None | Empty placeholder file; it is not used by the current application flow. |

CSV tool methods that exist but are not directly exposed by the router are describe_dataset, county_average_yield, and the metric helpers. The tool assumes the CSV schema includes yield_kg, county, crop, and rainfall_mm.

## 5. Dependencies and Environment Variables

| Dependency Source | Details |
| --- | --- |
| [pyproject.toml](pyproject.toml) | Runtime dependencies are faiss-cpu, langchain, langchain-community, langchain-google-genai, langchain-huggingface, pandas, pydantic, pypdf, python-dotenv, pyyaml, requests, rich, and sentence-transformers. |
| requirements.txt | Not present. Dependency management is handled through [pyproject.toml](pyproject.toml) and [uv.lock](uv.lock). |
| Environment loading | [src/config/settings.py](src/config/settings.py) calls dotenv.load_dotenv() on import. |
| Required environment variable | GOOGLE_API_KEY is needed for Gemini access. It is documented in [README.md](README.md), but the code does not explicitly validate that it is set at startup. |
| Weather API key | Not required. Open-Meteo is called without a separate credential. |
| Startup validation | There is no explicit startup validation for the config file, dataset paths, vector store files, or environment variables. |

## 6. Known Issues, TODOs, Hardcoded Values, and Missing Error Handling

| Issue | Impact |
| --- | --- |
| [src/agents/router.py](src/agents/router.py) checks CSV keywords before weather keywords, and both lists contain rainfall. | Rainfall-related weather questions can be routed to the CSV path instead of weather. |
| [src/tools/csv_tool.py](src/tools/csv_tool.py) uses exact substring matching for only a small set of phrases. | Many routed CSV questions will still fall through to the refusal string even if they are clearly CSV-related. |
| [main.py](main.py) hardcodes the PDF directory, the CSV path, the summary truncation limit of 15000 characters, and the weather coordinates for Nairobi. | The app is less configurable and less reusable across datasets or locations. |
| [src/config/config_loader.py](src/config/config_loader.py) opens src/config/app.yaml via a relative path. | Running the app from a different working directory can break config loading. |
| [src/vectorstore/faiss_store.py](src/vectorstore/faiss_store.py) loads FAISS with allow_dangerous_deserialization=True. | Reloading the persisted index depends on untrusted pickle deserialization. |
| [src/loaders/document_loader.py](src/loaders/document_loader.py) only scans one directory level with Path.glob("*.pdf"). | Nested PDF folders are ignored. |
| [src/tools/csv_tool.py](src/tools/csv_tool.py) assumes yield_kg, county, crop, and rainfall_mm exist and are clean. | Missing columns or bad values will raise errors or produce misleading results. |
| [src/services/weather_service.py](src/services/weather_service.py) only does a raw requests.get plus raise_for_status(). | Network failures, timeouts, or schema changes are not handled gracefully. |
| [main.py](main.py) only logs CSV and PDF paths. | Summary and weather responses are not written to the interaction log. |
| [src/tools/pdf_tool.py](src/tools/pdf_tool.py), [src/retrieval/retriever.py](src/retrieval/retriever.py), and [src/parsers/qa_response.py](src/parsers/qa_response.py) are currently unused by the main flow. | The codebase contains dead or placeholder modules that add maintenance noise. |
| [src/chains/csv_analysis_chain.py](src/chains/csv_analysis_chain.py) imports StrOutputParser but does not use it. | Minor cleanup opportunity. |
| [structure](structure) is outdated. | It can mislead anyone who uses it as a source of truth for the current repository layout. |
| [data/outputs/rag_logs.json](data/outputs/rag_logs.json) is append-only. | The log file will continue growing unless it is rotated or pruned. |
| There is no error handling around PDF loading, embedding creation, vector store creation, or CSV loading. | Startup can fail with uncaught exceptions if inputs or dependencies are missing. |

## 7. Current Test Coverage

The [tests/](tests/) directory is empty, so there is no automated unit, integration, or end-to-end test coverage in the repository. The only execution probe is [test.py](test.py), which is a manual Open-Meteo request script rather than a maintained test suite. I did not find any test runner configuration such as pytest settings or fixtures.