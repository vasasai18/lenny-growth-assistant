import asyncio
import uuid

import asyncpg
import pytest
from fastapi.testclient import TestClient

from app.agents.lenny_agent import AgentResult
from app.agents.service import get_agent_service
from app.main import app


class FakeAgentService:
    async def run(self, provider_name, user_message, mode, history):  # type: ignore[no-untyped-def]
        content = (
            "# Grounded artifact\n\nEvidence-backed content [1]."
            if mode == "markdown"
            else "Evidence-backed answer [1]."
        )
        return AgentResult(
            content=content,
            provider=provider_name,
            model="fake-test-model",
            sources=[
                {
                    "citation_number": 1,
                    "chunk_id": "00000000-0000-0000-0000-000000000001",
                    "episode_title": "Test episode",
                    "guest_name": "Test guest",
                    "publication_date": "2026-01-01",
                    "timestamp_ref": "00:10:00–00:12:00",
                    "source_url": "https://example.com/test",
                    "similarity": 0.75,
                }
            ],
        )


@pytest.fixture(scope="module")
def client_and_sessions():  # type: ignore[no-untyped-def]
    app.dependency_overrides[get_agent_service] = lambda: FakeAgentService()
    created_ids: list[str] = []
    with TestClient(app) as client:
        yield client, created_ids

    app.dependency_overrides.clear()

    async def cleanup() -> None:
        if not created_ids:
            return
        connection = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="lenny",
            password="change-me-locally",
            database="lenny_growth",
        )
        try:
            await connection.execute(
                "DELETE FROM sessions WHERE id = ANY($1::uuid[])",
                [uuid.UUID(value) for value in created_ids],
            )
        finally:
            await connection.close()

    asyncio.run(cleanup())


def create_session(client: TestClient, created_ids: list[str], title: str = "New chat") -> dict:
    response = client.post("/api/sessions", json={"title": title})
    assert response.status_code == 201
    payload = response.json()
    created_ids.append(payload["id"])
    return payload


def test_health_reports_all_components(client_and_sessions) -> None:  # type: ignore[no-untyped-def]
    client, _ = client_and_sessions

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["api"]["status"] == "healthy"
    assert payload["database"]["status"] == "healthy"
    assert payload["ollama"]["status"] == "healthy"
    assert payload["vector_store"]["status"] == "healthy"
    assert "2198 chunks" in payload["vector_store"]["detail"]


def test_session_creation_and_isolation(client_and_sessions) -> None:  # type: ignore[no-untyped-def]
    client, created_ids = client_and_sessions
    first = create_session(client, created_ids)
    second = create_session(client, created_ids, "Separate chat")

    chat_response = client.post(
        "/api/chat",
        json={
            "session_id": first["id"],
            "message": "How should teams prioritize?",
            "provider": "ollama",
            "mode": "answer",
        },
    )
    assert chat_response.status_code == 200, chat_response.text

    first_history = client.get(f"/api/sessions/{first['id']}").json()
    second_history = client.get(f"/api/sessions/{second['id']}").json()
    assert [message["role"] for message in first_history["messages"]] == [
        "user",
        "assistant",
    ]
    assert first_history["messages"][1]["sources"][0]["episode_title"] == "Test episode"
    assert second_history["messages"] == []


def test_message_and_markdown_artifact_persistence(client_and_sessions) -> None:  # type: ignore[no-untyped-def]
    client, created_ids = client_and_sessions
    session = create_session(client, created_ids)

    response = client.post(
        "/api/chat",
        json={
            "session_id": session["id"],
            "message": "Create a product strategy memo.",
            "provider": "ollama",
            "mode": "markdown",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["message"]["content"].startswith("# Grounded artifact")
    assert payload["artifact"]["artifact_type"] == "markdown"
    artifact_id = payload["artifact"]["id"]

    artifact_response = client.get(f"/api/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    assert artifact_response.json()["content"] == payload["artifact"]["content"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"session_id": "not-a-uuid", "message": "Question"},
        {
            "session_id": "00000000-0000-0000-0000-000000000001",
            "message": "",
        },
        {
            "session_id": "00000000-0000-0000-0000-000000000001",
            "message": "Question",
            "provider": "unknown",
        },
    ],
)
def test_chat_input_validation(client_and_sessions, body) -> None:  # type: ignore[no-untyped-def]
    client, _ = client_and_sessions

    response = client.post("/api/chat", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.headers["X-Request-ID"]


def test_missing_session_returns_structured_404(client_and_sessions) -> None:  # type: ignore[no-untyped-def]
    client, _ = client_and_sessions

    response = client.get("/api/sessions/00000000-0000-0000-0000-000000000099")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["request_id"]

