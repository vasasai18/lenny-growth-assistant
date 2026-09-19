# Agent Transcript 03: Transcript Ingestion

## Goal

Download a permitted transcript dataset, parse its metadata, create overlapping chunks, generate local embeddings, and store traceable vectors safely in PostgreSQL.

## Source and licensing decision

The project uses the public starter pack from `LennysNewsletter/lennys-newsletterpodcastdata`, Lenny's official GitHub organization. It contains 50 podcast transcripts plus structured metadata. Its license permits personal, non-commercial projects but prohibits redistributing the raw starter files. The raw `data/` directory is therefore Git-ignored; the public project will ship only the downloader and ingestion code.

The source Git commit is stored on every ingested row so an evaluator can identify the exact dataset version.

## Chunking decisions

- Target approximately 650 tokens, within the requested 500–800 range.
- Retain approximately 100 tokens from the preceding chunk.
- Keep speaker/timestamp paragraphs intact where possible.
- Record the first and last timestamps in each chunk.
- Use a stable regex token estimate so ingestion does not require a cloud tokenizer.
- Hash source URL, chunk position, and content for deterministic reruns.

## Embedding decisions

- Use local Ollama `nomic-embed-text`.
- Validate every returned embedding has exactly 768 dimensions before insertion.
- Batch requests and commit completed batches so an interrupted long run can resume.
- Create an HNSW cosine index after storage.

## Failure: database was stopped

**Problem:** The first one-episode ingestion could not connect to port 5433.

**Why:** The Phase 2 database container was no longer running.

**Fix:** Start `db` with Docker Compose and wait for its health check.

**Verification:** One transcript produced and stored 32 chunks.

## Failure: duplicate source chunks

**Problem:** Full ingestion reached a uniqueness violation for `content_hash`.

**Why:** The starter dataset contains duplicate content/source combinations. The initial loader deduplicated against rows already in PostgreSQL but not duplicates within the same newly prepared batch.

**Fix:** Deduplicate all prepared chunks by deterministic hash before querying or embedding. Retain already committed batches and resume safely.

**Verification:** Full ingestion stored 2,198 unique chunks from 50 episodes. A clean rerun reported `Unchanged chunks: 2198` and `New chunks to embed: 0`. All chunks include guest, publication date, and timestamp metadata; 98.6% are within 500–800 estimated tokens, with shorter values limited to natural final episode chunks.

## Failure: overlapping ingestion processes

**Problem:** A second rerun saw uniqueness conflicts even after input deduplication.

**Why:** The terminal session returned before its long-running child process finished, and another ingestion run started concurrently.

**Fix:** Stop only the stale ingestion PID and use PostgreSQL `ON CONFLICT DO NOTHING` for atomic, concurrency-safe inserts.

**Verification:** One process completed all 50 episodes. The next run required zero embeddings and retained exactly 2,198 unique hashes.
