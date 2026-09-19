# Agent Transcript 09: Ship 30 Writing Skill

## Goal

Implement the assessment's approximately 1,250-word Ship 30 for 30 output as a dedicated reusable skill rather than a phrase added to the normal chat prompt.

## Source principles

Ship 30's public guides emphasize a headline that makes the audience, topic, and promise clear; a strong single-sentence opener; consistent section patterns such as steps or lessons; skimmable short paragraphs; bullets; and an actionable takeaway. The assessment intentionally expands the usual short Atomic Essay format to approximately 1,250 words.

## Skill contract

- Target 1,250 words; accept 1,000–1,500 as approximately compliant.
- One H1 promise-driven headline.
- A specific one-sentence hook.
- At least three consistently patterned H2 sections.
- Short paragraphs, bullets, and selective bold emphasis.
- End with a framework, checklist, takeaway, or immediate action.
- Use only retrieved transcript excerpts.
- Cite factual claims with valid source numbers.
- Omit claims or sections that the evidence cannot support.

## Validation

The deterministic validator checks word range, headline, H2 count, bullets, emphasis, actionable ending, citation presence/range, paragraph length, and rejects external bibliography or author-year citation styles. A quote guard compares every direct quotation with the retrieved transcript text and removes unsupported quoted sentences. It cannot prove semantic entailment for every paraphrase by itself; grounding is additionally controlled through retrieval, an evidence-only prompt, and traceable citations.

## Local verification

The real `llama3.2:3b` fallback produced 1,244 words from six retrieved sources. Manual QA found an unsupported famous quote despite the prompt, which led to the deterministic quote guard. After that guard, the same output contained 1,114 words, remained structurally valid, and the unsupported sentence was absent. The complete backend suite passed: 40 tests with one dependency deprecation warning.

## Routing

Local Ollama's `ship30` mode calls `Ship30Writer.generate()` directly after retrieval. The Claude Agent SDK tool receives the exact same `Ship30Writer.output_contract()`, preventing the cloud and local writing rules from drifting.
