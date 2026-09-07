# Product Requirements Document

## Discovery brief

**Primary user:** a Growth PM or product leader who needs tactics from Lenny's Podcast but cannot listen to hundreds of hours of episodes. Their job is to turn recurring product and growth questions into decisions, plans, and shareable internal content. The assistant removes search/listening overhead while retaining traceability to a source.

**Success metrics:** at least 90% evaluator-rated citation accuracy; local Ollama time-to-first-answer under four seconds on the target machine for a normal question; zero known XSS escapes in the artifact viewer; 95% of valid requests receive either a cited answer or the explicit insufficiency response.

**Assumptions:** transcripts are public and may be processed for internal evaluation; the evaluator can run Docker and optionally Ollama; source metadata is available or can be derived. A small fixture corpus is shipped so first-run testing does not depend on a network download.

**In scope:** independent chat sessions, source-grounded QA, local/cloud model switch, Ship 30 writing mode, artifact previews, persistence, health state, logs, docs, automated tests. **Out of scope:** authentication/RBAC, multi-tenant isolation, web crawling, real-time transcript refresh scheduling, and using sources outside the archive. These are excluded to keep a demonstrable forward-deployment slice.

## Key flows and acceptance criteria

1. A user starts a session, asks a product question, and gets an answer with episode, guest, and timestamp citations.
2. A question with no relevant evidence returns the exact insufficiency behavior rather than fabricated advice.
3. A user changes Local Ollama to OpenAI without redeploying; the active choice is returned in the API response.
4. A user selects Ship 30 or artifact mode and views the result in the adjacent panel.
5. Restarting the stack preserves conversation rows in PostgreSQL.

## Risks and trade-offs

Local models keep demo cost and data exposure low but may reason less reliably than cloud models. Strict retrieval prevents unsupported claims but increases “insufficient information” responses. pgvector HNSW provides fast retrieval at the cost of write/index maintenance. Sanitizing plus sandboxing artifacts limits rich interactive output but protects the application shell.
