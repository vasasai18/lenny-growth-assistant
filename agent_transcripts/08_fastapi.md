# Agent Transcript 08: FastAPI and Persistence

## Goal

Expose stable HTTP APIs for sessions, grounded chat, artifacts, and component health while preserving independent conversation history.

## Endpoints

- `POST /api/sessions` creates a persistent chat session.
- `GET /api/sessions` lists recent sessions.
- `GET /api/sessions/{session_id}` returns messages, sources, and artifacts.
- `POST /api/chat` validates input, saves the user message, routes the explicit provider/mode, and saves the assistant result.
- `GET /api/artifacts/{artifact_id}` retrieves a generated artifact.
- `GET /api/health` reports API, database, pgvector/chunk count, and Ollama separately.

## Error contract

All handled errors use an `error` object with a stable code, plain-language message, request ID, and optional details. Validation returns 422, missing resources return 404, missing provider configuration returns 400, provider unavailability returns 503, model timeout returns 504, upstream response failures return 502, and unexpected failures return 500.

## Persistence decisions

- The user message commits before model generation so a failed request is not lost.
- The assistant message, sources, and optional artifact commit together.
- Only messages from the requested session enter its bounded history.
- The default `New chat` title becomes the first user message, truncated to 80 characters.
- Foreign-key cascades remove messages and artifacts if a session is deleted in future administration workflows.

## Observability

JSON logs include event, timestamp, level, request ID, method, path, status, latency, provider, mode, session ID, and error code where applicable. Full prompts, transcript text, generated content, and keys are not logged.

## Testing approach

Integration tests use the real PostgreSQL database and dependency-inject a fake agent. They verify health, session creation, isolation, message/source persistence, artifact persistence, input validation, structured 404 errors, and request IDs. Test sessions are deleted afterward.

