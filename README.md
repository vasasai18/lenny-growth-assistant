# The Lenny Growth Assistant

A full-stack RAG assistant that turns Lenny's Podcast transcripts into grounded product and growth answers, Ship 30 for 30 essays, and safe in-app artifacts.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000`. The required local model demo uses Ollama:

```bash
ollama pull llama3.2:3b
ollama serve
```

The backend is at `http://localhost:8000`; verify with `curl http://localhost:8000/api/health`.

## What works without external keys

The project includes representative local transcript fixtures, a fully functional chat UI, sessions in PostgreSQL, grounded retrieval, citations, and a model-unavailable fallback summary. This makes the evaluator path predictable. For production, run `backend/scripts/download_transcripts.py`, chunk/index the repository with `ingest.py`, and replace the demo lexical retriever with pgvector + embeddings (the database image is already pgvector-ready).

## Model selection

Choose **Local: Ollama** for the mandatory demonstration. Choose **Cloud: OpenAI** after setting `OPENAI_API_KEY`. Provider selection is per request; changing it requires no application-code changes. Cloud failures and missing keys fall back to source summaries rather than hiding retrieved evidence.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/sessions` | Create independent conversation context |
| GET | `/api/sessions/{id}` | Read persisted history |
| POST | `/api/chat` | Grounded answer, Ship 30 essay, or artifact |
| GET | `/api/health` | DB/configuration/Ollama status |

## Test

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Safety

Retrieved transcript snippets, not model memory, are the only supplied knowledge context. HTML artifacts are sanitized with DOMPurify and rendered in an iframe with `sandbox="allow-scripts"`; it deliberately omits `allow-same-origin`, blocking parent cookies, local storage, and DOM access. Scripts, forms, nested frames, and inline event handlers are removed before preview.

## Troubleshooting

- **Ollama unavailable:** run `ollama serve`; use the status from `/api/health`.
- **Port conflict:** change the host-side port in `docker-compose.yml`.
- **No answer:** this is correct for topics absent from the loaded archive; ingest more transcripts.
- **Docker unavailable:** run the backend commands above and `cd frontend && npm install && npm run dev` in a second terminal.

