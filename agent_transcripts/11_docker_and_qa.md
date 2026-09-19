# Agent Transcript 11: Docker and QA

The production topology uses PostgreSQL/pgvector, FastAPI, and an Nginx-served React build. Ollama stays on macOS for Apple acceleration and is reached from the backend container through `host.docker.internal:11434`. Health checks gate service startup. The test plan combines backend unit/integration coverage, frontend security/build checks, Compose health checks, and the documented manual UI checklist.
