import asyncio
import uuid
from collections.abc import AsyncIterator, Sequence
from datetime import date

from app.providers import BaseLLMProvider, ChatMessage
from app.rag.retriever import RetrievedChunk
from app.skills.ship30_writer import Ship30Writer


def evidence() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            episode_title="Product strategy",
            guest_name="Test Guest",
            publication_date=date(2026, 1, 1),
            timestamp_ref="00:10:00–00:12:00",
            source_url="https://example.com/episode",
            chunk_text="Teams learn by shipping small tests and listening to users.",
            similarity=0.8,
        )
    ]


def valid_essay() -> str:
    repeated_paragraphs = "\n\n".join(
        "Teams learn through focused experiments and direct customer feedback " * 10 + "[1]."
        for _ in range(11)
    )
    return f"""# 3 Product Experiments That Help Teams Choose What to Build

The safest product roadmap begins with a small, uncomfortable test.

## Lesson 1: Make the uncertainty visible

**Start with the decision**, not a pile of feature ideas [1].

{repeated_paragraphs}

## Lesson 2: Ship the smallest useful test

Use evidence to reduce uncertainty before increasing investment [1].

- Name the riskiest assumption.
- Build one focused test.
- Review what users actually did.

## Lesson 3: Turn feedback into the next decision

**Evidence changes the roadmap** when the team agrees what it means [1].

## Action Checklist

- Write the decision in one sentence.
- Match one test to one uncertainty.
- Decide the next action before collecting results.
"""


def test_valid_ship30_essay_passes_contract() -> None:
    result = Ship30Writer.validate(valid_essay(), source_count=1)

    assert result.valid, result.errors
    assert 1000 <= result.word_count <= 1500


def test_short_unstructured_uncited_output_fails() -> None:
    result = Ship30Writer.validate("A short answer.", source_count=2)

    assert not result.valid
    assert any("Word count" in error for error in result.errors)
    assert any("headline" in error for error in result.errors)
    assert any("citations" in error for error in result.errors)


def test_unknown_citation_number_fails() -> None:
    result = Ship30Writer.validate(valid_essay().replace("[1]", "[9]"), source_count=1)

    assert not result.valid
    assert any("does not match" in error for error in result.errors)


def test_external_reference_style_fails_grounding_contract() -> None:
    essay = valid_essay() + "\n\nReferences:\nSomeone (Smith, 2024)."

    result = Ship30Writer.validate(essay, source_count=1)

    assert not result.valid
    assert any("References section" in error for error in result.errors)
    assert any("author-year" in error for error in result.errors)


def test_unsupported_quote_is_removed_but_transcript_quote_is_kept() -> None:
    content = (
        '# Title\n\n"Teams learn by shipping small tests" [1].\n\n'
        '"A famous quote that is not in the transcript" [1].'
    )

    cleaned = Ship30Writer._remove_unsupported_quotes(content, evidence())

    assert "Teams learn by shipping small tests" in cleaned
    assert "famous quote" not in cleaned


class RecordingProvider(BaseLLMProvider):
    name = "test"
    model = "test-model"

    def __init__(self) -> None:
        self.system_prompt = ""
        self.messages: Sequence[ChatMessage] = ()
        self.calls = 0

    async def stream(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        self.system_prompt = system_prompt
        self.messages = messages
        self.calls += 1
        yield valid_essay()


def test_generate_uses_dedicated_skill_prompt_and_evidence() -> None:
    provider = RecordingProvider()

    output = asyncio.run(
        Ship30Writer().generate(provider, "How should teams test ideas?", evidence())
    )

    assert output.startswith("# 3 Product Experiments")
    assert "dedicated Ship 30 for 30 writing skill" in provider.system_prompt
    assert "Teams learn by shipping small tests" in provider.system_prompt
    assert "approximately 1250-word essay" in provider.messages[-1].content
    assert provider.calls == 1


class RepairingProvider(RecordingProvider):
    async def stream(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        self.system_prompt = system_prompt
        self.messages = messages
        self.calls += 1
        yield "Too short." if self.calls == 1 else valid_essay()


def test_generate_repairs_a_noncompliant_first_draft_once() -> None:
    provider = RepairingProvider()

    output = asyncio.run(
        Ship30Writer().generate(provider, "How should teams test ideas?", evidence())
    )

    assert provider.calls == 2
    assert Ship30Writer.validate(output, source_count=1).valid
    assert "FAILED RULES" in provider.messages[-1].content
