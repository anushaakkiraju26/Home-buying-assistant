# Home Buying Assistant

A source-grounded home-buying education assistant built with Streamlit,
LangChain, Anthropic, and Pinecone. The assistant searches a curated reference
library before answering and cites the documents used in each response.

> Haven provides general educational information. It is not a substitute for
> legal, tax, lending, or financial advice from a qualified professional.

## Features

- Streamlit chat interface with suggested questions and conversation history
- Hybrid retrieval using Pinecone semantic search and local BM25 keyword search
- Reciprocal-rank fusion and Pinecone reranking
- Answers grounded in retrieved context with inline source citations
- Expandable source excerpts in the UI
- FastAPI endpoints for retrieval and agent integrations
- Repeatable ingestion for PDF, HTML, Markdown, and text documents

## Architecture

```text
Question
   │
   ├── Pinecone semantic retrieval
   └── Local BM25 keyword retrieval
              │
              ▼
      Reciprocal-rank fusion
              │
              ▼
        Pinecone reranking
              │
              ▼
   Anthropic grounded response
              │
              ▼
     Answer with citations
```

## Project structure

```text
.
├── streamlit_app.py       # Streamlit Q&A interface
├── api.py                 # FastAPI retrieval and answer endpoints
├── ingest.py              # Document loading, chunking, and indexing
├── hybrid_retriever.py    # Hybrid retrieval and reranking
├── bm25_retriever.py      # Local keyword retrieval
├── retrieve.py            # Pinecone semantic retrieval
├── ask.py                 # Command-line Q&A entry point
├── chunks.json            # Local chunk corpus used by BM25
├── reference_documents/   # Canonical reference PDFs and web documents
├── ui/                    # FastAPI-served web interface
└── .streamlit/            # Streamlit theme configuration
```

## Prerequisites

- Python 3.9 or newer
- A Pinecone account and index
- An Anthropic API key

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/anushaakkiraju26/Home-buying-assistant.git
cd Home-buying-assistant

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local `.env` file:

```dotenv
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional
ANTHROPIC_MODEL=claude-sonnet-4-6
RAG_SERVICE_API_KEY=your_service_api_key
```

Never commit `.env`. It is excluded by `.gitignore`.

## Run the Streamlit UI

```bash
source .venv/bin/activate
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

## Run the FastAPI service

```bash
source .venv/bin/activate
uvicorn api:app --reload --port 8000
```

Useful URLs:

- Web interface: [http://localhost:8000](http://localhost:8000)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

Example retrieval request:

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question":"What should I know about HOA fees?"}'
```

## Update the reference library

Add supported files to `reference_documents/`:

- `.pdf`
- `.html` or `.htm`
- `.txt`
- `.md`

Then rebuild `chunks.json` and upload the expanded corpus to Pinecone:

```bash
source .venv/bin/activate
python ingest.py reference_documents
```

The ingestion process:

1. Loads all supported files recursively.
2. Extracts text and document metadata.
3. Splits content into overlapping chunks.
4. Creates stable IDs for the chunks.
5. Rebuilds the local `chunks.json` corpus.
6. Embeds and uploads the chunks to the `recursive-v1` Pinecone namespace.

After verifying ingestion, commit both the reference documents and updated
chunk corpus:

```bash
git add reference_documents chunks.json
git commit -m "Update home-buying reference library"
git push origin main
```

## Command-line Q&A

```bash
python ask.py "What costs should I expect at closing?"
```

## API endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | `GET` | Service health check |
| `/retrieve` | `POST` | Structured context and retrieved documents |
| `/tool` | `POST` | Plain-text context for agent tools |
| `/ask` | `POST` | Grounded answer with structured source documents |

## Security

- Do not commit `.env`, API keys, tokens, or `.streamlit/secrets.toml`.
- Use a secret manager or hosting-provider environment variables in production.
- Set `RAG_SERVICE_API_KEY` when exposing the FastAPI service publicly.
- Review document redistribution rights before adding new reference material.
