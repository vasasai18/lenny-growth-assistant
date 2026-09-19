# Agent Transcript 05: Ollama Validation

## Goal

Verify the mandatory local LLM independently before integrating it behind the application's provider interface.

## Checks

- Ollama HTTP API is reachable.
- `llama3.2:3b` chat model is installed.
- `nomic-embed-text` embedding model is installed.
- The embedding endpoint returns exactly 768 dimensions.
- The chat endpoint streams non-empty token content.
- First-token and total response times are measured on the target Mac.
- Connection, timeout, HTTP, missing-model, malformed-JSON, and empty-output errors have plain-language messages.

## Configuration

- Development URL: `http://localhost:11434`
- Docker-to-host URL: `http://host.docker.internal:11434`
- Chat model: `llama3.2:3b`
- Embedding model: `nomic-embed-text`
- Timeout: 120 seconds

## Measured result on the target Mac

- Cold first token: 21.65 seconds while loading the model into memory.
- Warm first token: 0.10 seconds.
- Warm total response: 0.58 seconds for the short verification sentence.
- Embedding dimension: 768.
- Streaming content: valid and non-empty.

The demo should run one warm-up request before recording. This keeps the visible local response fast without misrepresenting the cold-start trade-off.
