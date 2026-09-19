import asyncio

from scripts import bootstrap_hosted


def test_hosted_bootstrap_resumes_existing_database(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[str] = []

    async def count() -> int:
        return 12

    async def ingest() -> None:
        calls.append("ingest")

    def download(*_args) -> None:  # type: ignore[no-untyped-def]
        calls.append("download")

    async def close() -> None:
        calls.append("close")

    monkeypatch.setattr(bootstrap_hosted, "chunk_count", count)
    monkeypatch.setattr(bootstrap_hosted, "download", download)
    monkeypatch.setattr(bootstrap_hosted, "ingest", ingest)
    monkeypatch.setattr(bootstrap_hosted, "close_database", close)

    asyncio.run(bootstrap_hosted.bootstrap())

    assert calls == ["download", "ingest", "close"]
