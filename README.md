# The Lenny Growth Assistant

A full-stack, source-grounded assistant for product and growth questions. It searches Lenny's Podcast transcripts with PostgreSQL/pgvector, answers with visible citations, preserves independent sessions, creates Ship 30 essays and artifacts, and switches between local Ollama and cloud Anthropic at runtime.

## Features

- React, Vite, TypeScript, Tailwind CSS frontend
- FastAPI, Pydantic, async SQLAlchemy backend
- PostgreSQL 16, pgvector, and an HNSW cosine index
- Idempotent transcript download, chunking, local embedding, and ingestion
- Local `llama3.2:3b` plus `nomic-embed-text` through Ollama
- Anthropic Claude Agent SDK with four allowlisted product tools
- Persistent sessions, messages, citations, and artifacts
- Dedicated approximately 1,250-word Ship 30 skill
- Markdown preview and defense-in-depth HTML/CSS sandbox
- Structured JSON logs, typed errors, component health checks, tests, and Docker Compose

## Architecture

```text
Browser → React/Nginx → FastAPI → Agent route → pgvector retrieval
                                      ├── Ollama on the macOS host
                                      └── Claude Agent SDK → Anthropic

Transcript repository → ingestion CLI → Ollama embeddings → PostgreSQL/pgvector
```

The browser never receives provider keys or database credentials. Provider selection is explicit per request and never silently falls back. Read [architecture](docs/architecture.md), [PRD](docs/PRD.md), and [design](docs/design.md).

## Prerequisites

- macOS, Git, Python 3.11+, Node.js 20 or 22 LTS
- Docker Desktop with Docker Compose
- Ollama

Check from any Terminal folder:

```bash
git --version
python3 --version
node --version
npm --version
docker --version
docker compose version
ollama --version
```

With Homebrew, install missing tools using `brew install git python@3.12 node@22 ollama` and `brew install --cask docker`. Open Docker Desktop once afterward.

## Clone and configure

Terminal folder: the parent folder where the project should live.

```bash
git clone https://github.com/vasasai18/lenny-growth-assistant.git
cd lenny-growth-assistant
cp .env.example .env
```

Expected result: Terminal is inside `lenny-growth-assistant` and `.env` exists. `.env` is ignored by Git.

## Ollama setup

Terminal folder: `lenny-growth-assistant`.

```bash
ollama serve
```

Keep it open. If Ollama already runs, “address already in use” only means a second server is unnecessary. In another Terminal:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
curl http://localhost:11434/api/tags
```

Expected result: JSON lists both models.

## Local development

Terminal folder: `lenny-growth-assistant`.

```bash
docker compose up -d db
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements-dev.txt
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

Expected result: `Application startup complete.` Verify [the health endpoint](http://localhost:8000/api/health).

### Download and ingest transcripts

Terminal folder: `lenny-growth-assistant`, with `.venv` active and PostgreSQL/Ollama running.

```bash
PYTHONPATH=backend python backend/scripts/download_transcripts.py
PYTHONPATH=backend python backend/scripts/ingest.py
```

The reference run parsed 50 files into 2,198 chunks using a roughly 650-token target and 100-token overlap. A second run safely skips unchanged chunks. Downloaded data stays under ignored `data/`; the repository contains reproducible ingestion code, not the corpus.

### Run the frontend

Terminal folder: `lenny-growth-assistant/frontend`.

```bash
npm install
npm run dev
```

Use Node 20 or 22 LTS. Node 26 is not supported by this pinned Vite toolchain. Open [http://localhost:5173](http://localhost:5173); development `/api` requests proxy to port 8000.

## Docker Compose

The evaluator-friendly workflow keeps Ollama on macOS for Apple acceleration:

```bash
docker compose up --build
```

Expected result: `db`, `backend`, and `frontend` start. Open [http://localhost:5173](http://localhost:5173). The backend container reaches Ollama at `http://host.docker.internal:11434`.

If ports are occupied:

```bash
BACKEND_PORT=8001 FRONTEND_PORT=5174 docker compose up --build
```

For a fresh database, run ingestion from the local Python environment; it connects through port 5433 to the same Compose volume.

## Free public deployment

The repository includes `render.yaml` and `Dockerfile.render` for a Render Blueprint. It creates one free web service serving React and FastAPI together, plus free PostgreSQL/pgvector. The hosted service uses lightweight MiniLM CPU embeddings because it cannot reach Ollama on your Mac; generation uses Anthropic. Render prompts for `ANTHROPIC_API_KEY` during first creation and never stores it in Git.

Open `https://dashboard.render.com/blueprints`, connect this repository, and deploy the Blueprint. Free services sleep after inactivity, so the first request can take about one minute. Render's free PostgreSQL offering may have limited retention; confirm the current dashboard terms before relying on it beyond this assessment.

## Cloud Anthropic

Cloud mode is optional locally. Put the key only in `.env`, then restart the backend:

```dotenv
ANTHROPIC_API_KEY=your_real_key_here
ANTHROPIC_MODEL=claude-sonnet-5
```

Cloud mode sends the question, bounded history, and retrieved excerpts to Anthropic. There is no automatic local-to-cloud fallback.

## Using the application

1. Click **New chat** and select **Local — Ollama** or **Cloud — Anthropic**.
2. Use **Answer** for grounded chat, **Ship 30** for long-form writing, or **Markdown**/**HTML/CSS** for artifacts.
3. Expand transcript sources below assistant messages.
4. Create another chat to verify independent history.

The refusal text is: `I do not have sufficient information in Lenny's Podcast archive to answer this.`

## API

- `GET /api/health`
- `POST /api/sessions`
- `GET /api/sessions` and `GET /api/sessions/{session_id}`
- `POST /api/chat`
- `GET /api/artifacts/{artifact_id}`
- OpenAPI UI: `http://localhost:8000/docs`

## Tests

Terminal folder: `lenny-growth-assistant`.

```bash
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q
.venv/bin/python -m compileall -q backend/app backend/scripts
docker build --target test -t lenny-growth-assistant-frontend-test frontend
docker compose config --quiet
```

Backend integration tests require the Compose database and Ollama. Follow the [manual UI checklist](docs/manual-testing-checklist.md).

## Artifact security

Generated HTML is untrusted. Backend allowlist sanitization removes scripts, handlers, embeds, forms, SVG/MathML, and remote CSS URLs before persistence. The frontend sanitizes again with DOMPurify, then uses `iframe srcdoc` with an empty `sandbox` and a network-blocking CSP. Markdown uses `react-markdown` + `remark-gfm` without raw HTML. JavaScript artifacts are intentionally unsupported.

## Observability

JSON logs include request ID, event, status, duration, provider, and mode without intentionally logging keys, full messages, or transcript text. Health reports API, database, Ollama, and vector store separately.

## Troubleshooting

### Port already in use

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

Stop the old process with `Ctrl+C`, or use alternate Compose ports above.

### Ollama unavailable from Docker

Verify `curl http://localhost:11434/api/tags`, ensure `.env` has `OLLAMA_DOCKER_BASE_URL=http://host.docker.internal:11434`, then run `docker compose up -d --build backend`.

### Database refused

Run `docker compose ps` and `docker compose logs db`. Local Python uses port 5433; containers use hostname `db` and port 5432.

### Cloud not configured

Add `ANTHROPIC_API_KEY` to `.env` and restart. Never commit `.env`.

### No transcript answers

Check `/api/health`. If vector-store detail reports zero chunks, run download and ingestion.

### Slow local responses

The first request loads the model. Ship 30 may take several minutes on an 8 GB Mac because it validates and may generate sections separately.

## Limitations and trade-offs

- The local 3B model is private and inexpensive but weaker/slower than cloud.
- The UI shows progress, but the final response is returned as one JSON result rather than token streaming.
- Citation numbers expose supplied evidence, but automation cannot prove perfect entailment for every paraphrase. Ship 30 direct quotes are checked against retrieved text.
- Authentication, teams, billing, audio transcription, and production high availability are excluded.
- Review transcript licensing before redistributing source files.

## Extending

Implement `BaseLLMProvider` for another model; register typed tools in `backend/app/agents/tools.py`; tune retrieval through `.env`; or add artifact types only with a matching validation and sandbox boundary.

## Submission evidence

- [Demo script](docs/demo-script.md)
- [Manual test checklist](docs/manual-testing-checklist.md)
- `agent_transcripts/` contains implementation and debugging records.

## Secret safety before publishing

```bash
git status --short
git check-ignore .env
git grep -n -E '(sk-ant-|ANTHROPIC_API_KEY=.+|OPENAI_API_KEY=.+)' -- ':!README.md' ':!.env.example'
```

Review every staged file before pushing.
