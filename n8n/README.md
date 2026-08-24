# Home Buying RAG AI Agent

The n8n Cloud workflow calls a separately hosted Python retrieval service. This avoids Pinecone Inference response issues in n8n Cloud and preserves the project's full retrieval pipeline:

```text
n8n Chat → HTTP retrieval → AI Agent → answer
                        │
                        └─ FastAPI service
                           ├─ Pinecone dense search
                           ├─ local BM25 search
                           ├─ reciprocal-rank fusion
                           └─ Pinecone reranking
```

## 1. Populate Pinecone

```bash
source .venv/bin/activate
python ingest.py reference_documents
```

The service searches the `recursive-v1` namespace. Its vector count should be close to the number of records in `chunks.json`.

## 2. Run the service locally

Install the updated dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn api:app --reload --port 8000
```

Then open `http://localhost:8000` to use the Haven Q&A interface. The web app
is served by FastAPI, so the browser never receives your Anthropic or Pinecone
credentials.

### Run the Streamlit interface

```bash
streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).
The Streamlit app connects directly to the existing hybrid retriever and keeps
conversation state for the current browser session.

Test it:

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question":"What should I know about HOA fees?"}'
```

The retrieval response contains `context` with numbered source blocks and a structured `documents` list.

## 3. Deploy the service

### No-account testing with a temporary tunnel

You can test from n8n Cloud without creating a hosting account. Keep the API running locally in one terminal:

```bash
source .venv/bin/activate
uvicorn api:app --host 127.0.0.1 --port 8000
```

In a second terminal, start a free Cloudflare Quick Tunnel:

```bash
cloudflared tunnel --url http://localhost:8000
```

No Cloudflare account is required. Copy the generated `https://...trycloudflare.com` URL into the n8n HTTP Request Tool and append `/retrieve`.

Both terminal processes must remain running and the computer must stay awake. The public URL changes whenever the tunnel restarts, so this option is for development and testing only.

### Persistent hosting

The included `Dockerfile` works with container hosts such as Render, Railway, Fly.io, or Google Cloud Run. Configure these environment variables on the host:

```text
PINECONE_API_KEY
PINECONE_INDEX_NAME
RAG_SERVICE_API_KEY   # optional but strongly recommended
```

The deployment must also include `chunks.json`, because BM25 runs inside the service. The image intentionally excludes the original `data/` files because retrieval only needs `chunks.json` and Pinecone.

Do not commit `.env`; it is excluded from the container build.

## 4. Configure n8n

1. Import `home-buying-rag.json` as a new workflow.
2. Select your native Anthropic API credential in **Anthropic Chat Model**.
3. In **Retrieve Home Buying Context**, replace:

   ```text
   https://REPLACE_WITH_RAG_SERVICE_HOST/retrieve
   ```

   with the deployed HTTPS URL.
4. If `RAG_SERVICE_API_KEY` is set, add this header to the HTTP Request node:

   ```text
   Authorization: Bearer YOUR_RAG_SERVICE_API_KEY
   ```

   Prefer an n8n Header Auth credential rather than storing the key directly in the node.
5. Save, open **Chat**, and ask a question.

The regular HTTP Request node retrieves context before the AI Agent runs. This avoids the `supplyData` error that occurs when an AI HTTP Tool sub-node is executed as a normal step. The agent receives the numbered context directly in its prompt and is instructed to answer only from it.

## API

### `GET /health`

Returns `{"status":"ok"}`.

### `POST /retrieve`

```json
{
  "question": "What should I know about HOA fees?",
  "k": 20,
  "rerank_top_n": 5
}
```

`k` accepts 1–50 and `rerank_top_n` accepts 1–20.

### `POST /tool`

Accepts the same request body but returns only the numbered context as plain text. Use this endpoint for the n8n AI Agent HTTP tool; it avoids sending the model the much larger metadata payload from `/retrieve`.

### `POST /ask`

Accepts the same request body, retrieves relevant evidence, and returns a
grounded answer with structured source documents. The Haven web interface uses
this endpoint to render inline citations and source cards.
