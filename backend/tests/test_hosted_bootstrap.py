import asyncio

from scripts import bootstrap_hosted


def test_hosted_bootstrap_skips_existing_database(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[str] = []

    async def count() -> int:
        return 12

    async def never_ingest() -> None:
        calls.append("ingest")

    async def close() -> None:
        calls.append("close")

    monkeypatch.setattr(bootstrap_hosted, "chunk_count", count)
    monkeypatch.setattr(bootstrap_hosted, "ingest", never_ingest)
    monkeypatch.setattr(bootstrap_hosted, "close_database", close)

    asyncio.run(bootstrap_hosted.bootstrap())

    assert calls == ["close"]
