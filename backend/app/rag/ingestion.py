import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml


TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
TIMESTAMP_PATTERN = re.compile(r"\((\d{2}:\d{2}:\d{2})\)")
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True)
class Transcript:
    title: str
    guest: str | None
    publication_date: date | None
    source_url: str
    body: str
    source_file: Path


@dataclass(frozen=True)
class Chunk:
    episode_title: str
    guest_name: str | None
    publication_date: date | None
    timestamp_ref: str | None
    source_url: str
    chunk_index: int
    chunk_text: str
    content_hash: str


def estimate_tokens(text: str) -> int:
    """Return a stable, dependency-free approximation of model token count."""

    return len(TOKEN_PATTERN.findall(text))


def _parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def load_index(dataset_dir: Path) -> dict[str, dict]:
    index_path = dataset_dir / "index.json"
    with index_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return {item["filename"]: item for item in payload.get("podcasts", [])}


def parse_transcript(path: Path, dataset_dir: Path, index: dict[str, dict]) -> Transcript:
    raw = path.read_text(encoding="utf-8")
    metadata: dict = {}
    match = FRONTMATTER_PATTERN.match(raw)
    if match:
        metadata = yaml.safe_load(match.group(1)) or {}
        body = raw[match.end() :].strip()
    else:
        body = raw.strip()

    relative_path = path.relative_to(dataset_dir).as_posix()
    indexed = index.get(relative_path, {})
    title = str(metadata.get("title") or indexed.get("title") or path.stem)
    guest_value = metadata.get("guest") or indexed.get("guest")
    guest = str(guest_value) if guest_value else None
    source_url = str(
        metadata.get("post_url")
        or indexed.get("post_url")
        or f"https://github.com/LennysNewsletter/lennys-newsletterpodcastdata/blob/main/{relative_path}"
    )
    publication_date = _parse_date(metadata.get("date") or indexed.get("date"))

    if not body:
        raise ValueError(f"Transcript body is empty: {path}")

    return Transcript(
        title=title,
        guest=guest,
        publication_date=publication_date,
        source_url=source_url,
        body=body,
        source_file=path,
    )


def load_transcripts(dataset_dir: Path) -> list[Transcript]:
    index = load_index(dataset_dir)
    files = sorted((dataset_dir / "podcasts").glob("*.md"))
    if not files:
        raise FileNotFoundError(
            f"No transcripts found under {dataset_dir / 'podcasts'}. "
            "Run backend/scripts/download_transcripts.py first."
        )
    return [parse_transcript(path, dataset_dir, index) for path in files]


def _split_oversized_paragraph(paragraph: str, maximum_tokens: int) -> list[str]:
    words = paragraph.split()
    if estimate_tokens(paragraph) <= maximum_tokens:
        return [paragraph]

    parts: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and estimate_tokens(candidate) > maximum_tokens:
            parts.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        parts.append(" ".join(current))
    return parts


def _timestamp_reference(text: str) -> str | None:
    timestamps = TIMESTAMP_PATTERN.findall(text)
    if not timestamps:
        return None
    if len(timestamps) == 1 or timestamps[0] == timestamps[-1]:
        return timestamps[0]
    return f"{timestamps[0]}–{timestamps[-1]}"


def chunk_transcript(
    transcript: Transcript,
    target_tokens: int = 650,
    overlap_tokens: int = 100,
) -> list[Chunk]:
    if overlap_tokens >= target_tokens:
        raise ValueError("Chunk overlap must be smaller than the chunk target.")

    maximum_tokens = max(target_tokens + 150, target_tokens)
    paragraphs = [
        part
        for paragraph in re.split(r"\n\s*\n", transcript.body)
        if paragraph.strip()
        for part in _split_oversized_paragraph(paragraph.strip(), maximum_tokens)
    ]

    chunks: list[Chunk] = []
    start = 0
    while start < len(paragraphs):
        selected: list[str] = []
        token_count = 0
        end = start

        while end < len(paragraphs):
            paragraph_tokens = estimate_tokens(paragraphs[end])
            if selected and token_count + paragraph_tokens > maximum_tokens:
                break
            selected.append(paragraphs[end])
            token_count += paragraph_tokens
            end += 1
            if token_count >= target_tokens:
                break

        text = "\n\n".join(selected).strip()
        digest_input = f"{transcript.source_url}\n{len(chunks)}\n{text}".encode()
        chunks.append(
            Chunk(
                episode_title=transcript.title,
                guest_name=transcript.guest,
                publication_date=transcript.publication_date,
                timestamp_ref=_timestamp_reference(text),
                source_url=transcript.source_url,
                chunk_index=len(chunks),
                chunk_text=text,
                content_hash=hashlib.sha256(digest_input).hexdigest(),
            )
        )

        if end >= len(paragraphs):
            break

        retained_tokens = 0
        next_start = end
        while next_start > start and retained_tokens < overlap_tokens:
            next_start -= 1
            retained_tokens += estimate_tokens(paragraphs[next_start])
        start = next_start if next_start > start else end

    return chunks


def chunk_all(
    transcripts: list[Transcript], target_tokens: int, overlap_tokens: int
) -> list[Chunk]:
    return [
        chunk
        for transcript in transcripts
        for chunk in chunk_transcript(transcript, target_tokens, overlap_tokens)
    ]


def source_revision(dataset_dir: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=dataset_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()

