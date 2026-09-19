# Product Requirements Document: The Lenny Growth Assistant

## 1. Product summary

The Lenny Growth Assistant is a conversational research and writing application for product managers and growth practitioners. It answers questions using only indexed Lenny's Podcast transcripts, shows the supporting episodes, remembers context within each chat session, and turns grounded material into reusable Markdown or HTML artifacts.

This document is a discovery brief as well as a product specification. Unknowns are recorded as assumptions rather than hidden.

## 2. Primary user

The primary user is a product manager or growth lead who needs practical advice but does not have time to search or listen to hundreds of hours of podcast material.

The secondary user is an evaluator or client engineer who needs to install, verify, troubleshoot, and extend the application quickly.

## 3. Problem and pain point

Podcast transcripts contain useful operating knowledge, but they are long and fragmented across episodes. Ordinary chat models may answer fluently without proving that the answer came from the requested archive. The user needs fast synthesis, visible evidence, and reusable output without learning prompting or retrieval infrastructure.

## 4. Job to be done

When I have a product or growth question, help me find and combine relevant lessons from Lenny's Podcast, show me where each important claim came from, and let me turn the result into a polished artifact so I can make or communicate a decision confidently.

## 5. Success metrics

The assessment version targets:

- Citation correctness: at least 90% of sampled factual claims are supported by the cited retrieved chunk in a manual 20-question evaluation set.
- Grounding refusal: 100% of clearly unsupported evaluation questions return the documented insufficient-information response rather than invented transcript facts.
- Session isolation: 100% of automated session-isolation tests pass.
- Local usability: the first visible response token from `llama3.2:3b` arrives within 15 seconds on the target 8 GB Apple Silicon Mac for a typical grounded question. We use 15 seconds rather than the reference suggestion of 4 seconds because the actual target hardware has 8 GB RAM.
- Artifact safety: no executable parent-page access in the security checklist, and no known high-severity XSS issue in the viewer implementation.
- Operability: a new evaluator can reach a healthy application using the documented Docker workflow in no more than 15 minutes after prerequisites and models are available.

## 6. Assumptions

- The transcript source is public and may be downloaded and indexed for this assessment; source licensing and redistribution terms must be checked before publishing transcript data.
- The submitted repository will contain ingestion code, not a large copied transcript corpus, unless redistribution is clearly allowed.
- Ollama runs on the macOS host for the most reliable Apple Silicon acceleration. Docker services reach it through `host.docker.internal`.
- `llama3.2:3b` is the local chat model because the target Mac has 8 GB RAM.
- `nomic-embed-text` is the preferred local embedding model. We will verify its dimension before defining the pgvector column and index.
- Anthropic is the first cloud provider, and the official Claude Agent SDK provides the required cloud agent/tool loop.
- Each request explicitly includes its provider choice; changing providers does not rewrite earlier messages.
- English transcripts and English responses are the assessment scope.

## 7. Included scope

- Transcript ingestion with metadata extraction, token-aware chunking, overlap, deterministic reruns, embeddings, and pgvector storage.
- Grounded conversational retrieval with visible citations and a clear unsupported-answer response.
- Independent, persistent chat sessions and message history.
- Runtime Ollama/Anthropic selection with a visible provider badge.
- A cloud agent built with the Anthropic Claude Agent SDK and explicit tools for retrieval, Ship 30 writing, and artifacts.
- A local Ollama execution path using the same tool contracts and deterministic routing so the required demo does not depend on a cloud key.
- A dedicated approximately 1,250-word Ship 30 writing skill.
- Markdown and HTML/CSS artifact generation and side-by-side preview.
- FastAPI, PostgreSQL/pgvector, React/Vite/TypeScript, Tailwind CSS, Docker Compose, structured logs, tests, and handoff documentation.

## 8. Excluded scope

- User accounts, teams, billing, and production SSO. They add security and product work unrelated to the assessment's central evidence.
- Transcript audio transcription. The project consumes existing text transcripts.
- Web-wide search or general-knowledge fallback. It would weaken the strict grounding promise.
- Editing or publishing artifacts to third-party services.
- Production multi-region deployment, autoscaling, or high availability.
- Running Ollama inside Docker on macOS by default, because host execution is simpler and typically uses Apple acceleration more reliably.

## 9. Main user flow

1. The user opens the application and creates a new chat.
2. The user selects Local (Ollama) or Cloud (Anthropic).
3. The user asks a product or growth question.
4. The system embeds the query, retrieves relevant transcript chunks, and checks relevance.
5. If evidence is insufficient, the system says so and does not call unsupported facts true.
6. Otherwise, the agent/provider creates an answer constrained to the retrieved context.
7. The UI shows the answer and expandable episode citations.
8. A follow-up reuses only that session's history.
9. The user can request a Ship 30 essay, Markdown artifact, or HTML artifact.
10. The artifact opens in the right panel; HTML is sanitized and rendered in an isolated iframe.

## 10. Functional requirements

### Conversations and grounding

- Create and retrieve sessions through documented APIs.
- Persist user and assistant messages, timestamps, source metadata, and artifacts in PostgreSQL.
- Retrieve four to six chunks by cosine similarity, subject to a configured relevance threshold.
- Cite stable source metadata: episode, guest when available, timestamp or section when available, source URL, and chunk identifier.
- Use exactly the approved insufficient-information behavior when retrieval evidence is empty or weak.

### Providers and agent

- Support `ollama` and `anthropic` provider values without code changes.
- Make the active provider visible in every chat.
- Return useful errors for unavailable Ollama, missing cloud keys, timeouts, and malformed model responses.
- Use Claude Agent SDK custom tools on the Anthropic path.
- Keep tool inputs and outputs provider-neutral so the local path can expose the same product capabilities.

### Writing and artifacts

- Implement Ship 30 as a named, reusable service/tool with structure and grounding validation.
- Store artifacts separately from chat messages.
- Render Markdown with GitHub-Flavored Markdown support.
- Sanitize HTML and render it through `iframe srcdoc` with a restrictive sandbox and Content Security Policy.

## 11. Acceptance criteria

- `docker compose up --build` starts database, backend, and frontend after documented environment setup.
- `GET /api/health` reports API, database, pgvector, and Ollama status separately.
- A user can create two chats, send messages to both, reload, and see no history leakage.
- A grounded answer displays at least one source and every source links to stored transcript metadata.
- An out-of-domain question produces the insufficient-information response.
- Switching providers in the UI changes the provider used for the next request and the response records that provider.
- Missing provider services produce a friendly UI error and structured server log.
- Ship 30 output is approximately 1,250 words, structured, attributable, and based only on retrieved evidence.
- Markdown previews render safely; HTML cannot access the parent DOM, cookies, or local storage.
- Automated backend and frontend checks cover the critical requirements listed in the assignment.
- The repository contains no real secrets.

## 12. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Hallucinated transcript claims | Loss of trust | Retrieval threshold, context-only prompt, post-generation citation validation, refusal behavior, evaluation set |
| Weak 3B local-model reasoning | Lower answer quality | Smaller context, deterministic tool routing, low temperature, clear prompts, transparent local/cloud label |
| Slow local inference | Poor demo | Stream output, warm the model before demo, cap retrieved context and generation length |
| Embedding/model mismatch | Broken retrieval | Persist embedding model and dimension, verify them during startup and ingestion |
| Transcript source changes | Failed ingestion | Version source URLs/commit metadata, idempotent loader, parser tests and clear errors |
| Data leakage to cloud | Privacy concern | Provider choice is explicit; disclose that cloud mode sends the question, relevant history, and retrieved chunks to Anthropic |
| Generated HTML XSS | User compromise | DOMPurify, sandbox without `allow-same-origin`, restrictive CSP, no network access by default, size limits |
| Tool prompt injection in transcripts | Agent manipulation | Treat transcript text as quoted data, never instructions; fixed tool allowlist and no filesystem/shell tools in the web app |
| SDK/provider outage | Failed request | Timeouts, typed errors, health checks, no silent provider fallback |

## 13. Key trade-offs

- We favor evidence precision over answering every question. A refusal is better than an unsupported answer.
- We keep Ollama on the host instead of adding a fourth default container, improving Mac performance at the cost of one documented host prerequisite.
- We use a deterministic local tool route because a small local model is less reliable at autonomous tool selection. The Anthropic path demonstrates the required agent SDK; both paths use the same tool contracts.
- We begin with exact pgvector search because the assessment dataset is expected to be manageable. An HNSW cosine index is added when the corpus size and query plan justify it.

## 14. Implementation plan

1. Verify local prerequisites and models.
2. Create discovery, architecture, and design specifications.
3. Add PostgreSQL/pgvector and asynchronous database models.
4. Build idempotent transcript download, parsing, chunking, and embedding ingestion.
5. Implement retrieval, relevance checks, and citation contracts.
6. Integrate and independently verify Ollama.
7. Add provider abstraction and Anthropic cloud provider.
8. Add Claude Agent SDK tools and routing.
9. Implement FastAPI sessions, chat, artifacts, health, logs, and errors.
10. Implement and test Ship 30 and artifact services.
11. Build the accessible responsive frontend.
12. Run end-to-end, automated, security, and manual checks.
13. Finalize Docker, README, GitHub submission audit, and demo script.

