# Agent Transcript 01: Initial Scaffolding

## Goal

Translate the official Oogway Labs assignment into a concrete product, architecture, and UI plan before implementation.

## User direction

The user requested beginner-friendly, phase-by-phase implementation. Phase 0 verified the macOS environment. Phase 1 creates the folder structure, PRD, architecture, design specification, `.gitignore`, and `.env.example`.

## Decisions

- The official assignment is authoritative when it conflicts with the pasted reference document.
- Use Python 3.12 rather than the installed Python 3.14 for dependency compatibility.
- Use `llama3.2:3b` for local generation on the target 8 GB Apple Silicon Mac.
- Run Ollama on the macOS host and connect from Docker through `host.docker.internal`.
- Use the official Anthropic Claude Agent SDK for the compliant cloud agent path.
- Give cloud and local execution the same typed retrieval, writing, and artifact tool contracts.
- Use deterministic tool routing on the small local model path to improve reliability.
- Do not silently fall back between local and cloud providers.
- Block JavaScript in generated artifacts; sanitize HTML and isolate it in a sandboxed iframe.

## Correction made during planning

The pasted reference allowed LangChain or LlamaIndex primitives as the agent framework. The official assessment only permits the Anthropic Claude Agent SDK or Pi Coding Agent. The architecture follows the official requirement and does not treat a generic LLM wrapper as the required agent layer.

## Verification

- Confirm the expected folder structure exists.
- Confirm `.env.example` contains placeholders only.
- Confirm `.gitignore` excludes `.env`, local data, dependency folders, and runtime state.
- Confirm the three specification documents cover every discovery item requested by the assessment.

