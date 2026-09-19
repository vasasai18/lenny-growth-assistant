import asyncio
import json
import time

import httpx

from app.config import get_settings


class OllamaCheckError(RuntimeError):
    pass


async def check_ollama() -> None:
    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip("/")
    timeout = httpx.Timeout(settings.llm_timeout_seconds, connect=5.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            tags_response = await client.get(f"{base_url}/api/tags")
            tags_response.raise_for_status()
            models = {
                model["name"] for model in tags_response.json().get("models", [])
            }
            print(f"Ollama API: reachable at {base_url}")
            print(f"Installed models: {', '.join(sorted(models))}")

            required_models = {
                settings.ollama_chat_model,
                settings.ollama_embedding_model,
            }
            missing = {
                model
                for model in required_models
                if model not in models and f"{model}:latest" not in models
            }
            if missing:
                commands = ", ".join(f"ollama pull {model}" for model in sorted(missing))
                raise OllamaCheckError(f"Required model missing. Run: {commands}")

            embed_response = await client.post(
                f"{base_url}/api/embed",
                json={
                    "model": settings.ollama_embedding_model,
                    "input": ["product discovery"],
                },
            )
            embed_response.raise_for_status()
            embeddings = embed_response.json().get("embeddings", [])
            if len(embeddings) != 1:
                raise OllamaCheckError("Embedding API returned an unexpected response.")
            dimension = len(embeddings[0])
            if dimension != settings.embedding_dimension:
                raise OllamaCheckError(
                    f"Embedding dimension is {dimension}; expected "
                    f"{settings.embedding_dimension}."
                )
            print(f"Embedding check: {dimension} dimensions")

            prompt = (
                "Reply with one short sentence. State that local Ollama generation is "
                "working. Do not add a heading or explanation."
            )
            started_at = time.monotonic()
            first_token_seconds: float | None = None
            output_parts: list[str] = []

            async with client.stream(
                "POST",
                f"{base_url}/api/chat",
                json={
                    "model": settings.ollama_chat_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "options": {"temperature": 0},
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    payload = json.loads(line)
                    content = payload.get("message", {}).get("content", "")
                    if content:
                        if first_token_seconds is None:
                            first_token_seconds = time.monotonic() - started_at
                        output_parts.append(content)
                    if payload.get("done"):
                        break

            output = "".join(output_parts).strip()
            if not output or first_token_seconds is None:
                raise OllamaCheckError("Chat API completed without generated text.")

            elapsed = time.monotonic() - started_at
            print(f"Chat model: {settings.ollama_chat_model}")
            print(f"First token: {first_token_seconds:.2f} seconds")
            print(f"Total generation time: {elapsed:.2f} seconds")
            print(f"Model response: {output}")
            print("Streaming chat check: PASS")
            print("Ollama verification: PASS")
    except httpx.ConnectError as exc:
        raise OllamaCheckError(
            f"Ollama is not reachable at {base_url}. Open the Ollama app or run "
            "`ollama serve`, then retry."
        ) from exc
    except httpx.TimeoutException as exc:
        raise OllamaCheckError(
            f"Ollama did not respond within {settings.llm_timeout_seconds} seconds."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaCheckError(
            f"Ollama returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:300]}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise OllamaCheckError("Ollama returned malformed streaming JSON.") from exc


def main() -> None:
    try:
        asyncio.run(check_ollama())
    except OllamaCheckError as exc:
        print(f"Ollama verification: FAIL\n{exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

