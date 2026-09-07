# Agent transcript — initial scaffolding

Decision: use FastAPI, PostgreSQL/pgvector Docker image, and Vite React TypeScript. Implement provider interface behind one router and default to Ollama for the evaluator demo. Keep deterministic sample transcripts so the application can be evaluated without a network-dependent ingestion run.

Validation planned: health endpoint, retrieval/out-of-domain unit tests, API schema test, Docker Compose configuration review.
