# Agri Assistant

Agri Assistant is a production-style agricultural advisory platform built for location-aware crop guidance and document-grounded farm decision support. The project combines a FastAPI backend, retrieval-augmented generation, structured agronomic analytics, and a React frontend into a single end-to-end system for agricultural Q&A.

The application is designed around practical agronomy use cases such as:

- answering farmer questions using indexed PDF knowledge bases
- evaluating agronomic CSV datasets for seasonal and production insights
- checking climate and weather conditions for local recommendations
- serving contextual, location-aware answers for Kenyan counties and farm areas
- exposing health checks, caching, request tracking, and API endpoints for integration

## Overview

Agri Assistant brings together several layers:

- document ingestion and chunking for agricultural PDFs
- embeddings and vector retrieval for semantic search
- Groq-hosted LLM inference for answer generation
- Redis-backed caching and conversation/session tracking
- PostgreSQL with pgvector for structured data and retrieval support
- a Vite + React frontend for interactive county-based chats

This is no longer a simple CLI-only project. The system is structured as a multi-service app with a backend API and a frontend client, while still retaining the library-driven RAG logic used to answer agricultural questions.

## Core Features

- Retrieval-augmented answering from domain documents in `data/pdfs`
- Weather-driven guidance based on latitude and longitude using the Open-Meteo API
- CSV analysis for production and farm outcome data
- Per-request logging and request IDs for tracing
- Redis-based caching and short-term session memory
- Health monitoring for database, cache, and embedding services
- County-based UI selection for Kenyan regions
- Multi-audience response handling for farmers and experts
- English and Swahili output support in the API request schema

## Technology Stack

### Backend

- Python 3.12+
- FastAPI
- Pydantic + Pydantic Settings
- LangChain and LangChain Community
- Groq LLM integration via `langchain-groq`
- HuggingFace embeddings
- FAISS vector search
- PostgreSQL + pgvector
- Redis
- PyPDF, pandas, PyYAML, httpx, requests

### Frontend

- React 19
- Vite
- TypeScript
- Axios
- Lucide React

## Current Architecture

The project is organized into a backend API and client app:

- `src/api` handles FastAPI routes, request validation, and health checks
- `src/agents` contains the routing and orchestration logic for question handling
- `src/chains` includes the LangChain QA, summary, weather, and CSV analysis flows
- `src/retrieval` and `src/vectorstore` manage document retrieval and FAISS-based vector store access
- `src/ingestion` covers document and data ingestion patterns for tiered retrieval
- `src/cache` and `src/memory` manage Redis caching and conversational state
- `src/config` contains runtime configuration and the app YAML settings
- `client/` provides the React interface for county and chat interaction

## Project Structure

```text
agri-assistant/
├── client/                       # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── csv/
│   ├── db/
│   ├── pdfs/
│   └── vectorstore/
├── src/
│   ├── agents/
│   ├── api/
│   ├── cache/
│   ├── chains/
│   ├── config/
│   ├── embeddings/
│   ├── evaluation/
│   ├── ingestion/
│   ├── loaders/
│   ├── memory/
│   ├── parsers/
│   ├── processors/
│   ├── prompts/
│   ├── retrieval/
│   ├── services/
│   ├── tools/
│   └── vectorstore/
├── tests/
├── .env.example                 # optional example file if added locally
├── main.py
├── pyproject.toml
├── README.md
└── SUMMARY.md
```

## Prerequisites

Before running the app, make sure you have:

- Python 3.12 or later
- Node.js 18+ and npm
- Redis running locally or via a remote Redis instance
- PostgreSQL configured with pgvector support
- Internet access for LLM and weather API calls
- A valid Groq API key
- A Hugging Face token if your embedding setup requires one

## Environment Configuration

Create a `.env` file in the project root with the required variables:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://username:password@host:5432/agri_assistant
REDIS_URL=redis://localhost:6379/0
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
PDF_DIR=data/pdfs
CSV_PATH=data/csv/farm_production.csv
VECTORSTORE_DIR=data/vectorstore
```

The app loads default runtime settings from `src/config/app.yaml` as well:

```yaml
app:
  name: Agri Assistant

llm:
  provider: groq
  model: llama-3.3-70b-versatile
  temperature: 0.2

retrieval:
  top_k: 3
  similarity_threshold: 1.0

splitting:
  chunk_size: 1000
  chunk_overlap: 200

vectorstore:
  path: data/vectorstore
  rebuild: true
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd agri-assistant
```

### 2. Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

This project uses the package metadata in `pyproject.toml`, so the environment will install the required dependencies including:

- FAISS
- LangChain
- Groq integration
- PostgreSQL drivers
- Redis
- FastAPI
- pgvector support

### 4. Install frontend dependencies

```bash
cd client
npm install
```

## Running the Application

### Start the backend API

From the project root:

```bash
uvicorn src.api.main:app --reload --port 8000
```

The API exposes interactive docs at:

- http://localhost:8000/docs
- http://localhost:8000/redoc

### Start the frontend

From the `client` folder:

```bash
npm run dev
```

The frontend is typically served at:

- http://localhost:5173

## API Endpoints

### Health check

```http
GET /health
```

Returns service health status for:

- database connectivity
- Redis availability
- embedding service availability

### Ask a question

```http
POST /ask
```

Request body:

```json
{
  "question": "What are the best maize planting practices for this area?",
  "lat": -1.286389,
  "lon": 36.817223,
  "audience": "farmer",
  "language": "en",
  "session_id": "optional-session-id"
}
```

Response body:

```json
{
  "answer": "Based on the retrieved agronomic guidance...",
  "tools_invoked": ["weather", "document_retrieval", "csv_analysis"],
  "cache_hit": false,
  "latency_ms": 1125,
  "request_id": "3d2b71a6-1d74-4b1e-ae9d-1d7ce9dd3d7c",
  "session_id": "optional-session-id"
}
```

## Data and Retrieval Workflow

The system uses layered retrieval and reasoning:

1. PDFs are loaded from `data/pdfs`
2. Documents are split into chunks using the configured chunk size and overlap
3. Embeddings are created using the configured embedding service
4. Vector similarity search retrieves the most relevant chunks
5. The router decides whether to use document knowledge, CSV analytics, or weather guidance
6. The model synthesizes a final answer with context and local agricultural constraints

The vector store is configured via `src/config/app.yaml` and typically lives in `data/vectorstore`.

## Frontend Behavior

The current UI is built for county-based agricultural assistance and includes:

- county selection flow
- localStorage persistence for selected region
- chat interface for question asking
- region switch action while staying in chat context

The frontend is separate from the backend and requires the API to be running for live responses.

## Database and Cache Notes

This project is backed by external services that should be running in a development or production environment:

- PostgreSQL for persistence and vector-aware ingestion
- Redis for request caching and session state
- FAISS for local retrieval vectors

The backend health endpoint checks these dependencies automatically and marks the app as `ok`, `degraded`, or `error` depending on availability.

## Development Notes

- `src/config/settings.py` loads environment variables using `pydantic-settings`
- `src/config/app_config.py` validates app configuration from YAML
- `src/api/main.py` defines the FastAPI app and middleware setup
- `src/api/routers/health.py` and `src/api/routers/ask.py` provide the main API routes
- `tests/` includes validation for retrieval, logging, caching, and soil-related workflows

## Typical Local Workflow

1. Start Redis and PostgreSQL
2. Configure `.env`
3. Install dependencies
4. Run backend with `uvicorn src.api.main:app --reload --port 8000`
5. Run frontend with `cd client && npm run dev`
6. Open the frontend in the browser and ask a question
7. Use `/docs` to test API requests directly

## Troubleshooting

### Missing environment variables

If the app fails at startup, verify that the following are present in `.env`:

- `GROQ_API_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `HUGGINGFACEHUB_API_TOKEN`

### Redis unavailable

The app will continue to start but may operate in a degraded mode. Redis-backed caching and session support may be disabled if the service is not reachable.

### Database connectivity issues

Check that PostgreSQL is running and that `DATABASE_URL` points to a valid database with pgvector installed.

### Embedding or retrieval failures

Verify the embedding token and confirm the document source directory contains valid PDF content.

### Frontend cannot reach the API

Ensure the backend is running and the CORS configuration includes the frontend origin.

## Deployment Considerations

The backend is structured for deployment as a Python service, while the frontend can be deployed as a standalone Vite app. For a production deployment, you should:

- set secure environment variables in the hosting platform
- configure Redis and PostgreSQL connection strings for the target environment
- set the correct CORS origins
- enable proper logging and monitoring
- verify the app health route before exposing the service publicly

## Project Status

This repository is actively structured as a modern agricultural AI assistant with:

- backend API service
- retrieval pipeline
- frontend client
- database and cache integrations
- LLM and weather-based agronomic guidance

It is suitable for local development, testing, and extension into a fuller agronomy platform.

## Author

Created and maintained by Deo-Siatah.
