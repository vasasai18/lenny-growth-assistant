# Agent Transcript 06: Provider Abstraction

## Goal

Allow the application to select Ollama or Anthropic per request without changing chat, retrieval, or UI code.

## Design

- `BaseLLMProvider` defines one streaming contract and one convenience method that collects a complete response.
- `OllamaProvider` translates the contract to Ollama's NDJSON `/api/chat` stream.
- `AnthropicProvider` translates the same contract to Anthropic's official async Messages API stream.
- `create_provider()` accepts only `ollama` or `anthropic` and defaults to the configured provider.
- `claude-sonnet-4-6` is the cloud default used by the hosted Agent SDK integration.
- The provider is selected explicitly on each future chat request.

## Failure behavior

- Missing cloud key: clear configuration error and suggestion to choose Local.
- Unknown provider: validation error listing supported values.
- Connection failure: provider-unavailable error.
- Timeout: provider-timeout error.
- HTTP or malformed/empty stream: typed provider error.
- No silent fallback between providers. This prevents accidental transmission of locally intended content to a cloud API.

## Testing

Network transports are mocked for automated tests. Tests cover streaming assembly, malformed Ollama output, Ollama HTTP failure, the Anthropic streaming contract, runtime switching, missing cloud configuration, and unknown providers. A live smoke check calls only local Ollama because no cloud key is required.
