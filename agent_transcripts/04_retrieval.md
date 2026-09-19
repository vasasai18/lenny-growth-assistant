# Agent Transcript 04: Semantic Retrieval

## Goal

Retrieve the most relevant transcript chunks with pgvector, return traceable citation metadata, and refuse unsupported questions.

## Implementation

- Embed the current query with the same local `nomic-embed-text` model used for ingestion.
- Rank transcript chunks by pgvector cosine distance.
- Convert distance to a normalized cosine similarity score.
- Keep the top five chunks that meet the configured evidence threshold.
- Return episode, guest, date, timestamp, source URL, chunk ID, and similarity for citations.
- Wrap transcript excerpts in explicit quote markers so later agents treat them as data rather than instructions.
- Export one exact insufficient-information message for all unsupported-answer paths.

## Threshold calibration

The initial planning value was 0.45. Live measurements showed:

- A relevant product question produced top scores from 0.6323 to 0.6546.
- A capital-city question produced a maximum score of 0.3863.
- A leaking-faucet question produced a misleading maximum of 0.4704 because a sales transcript contained the phrase “kitchen sink.”

The default threshold was raised to 0.52. This is high enough to reject the tested lexical accidents while retaining the tested product evidence. It remains configurable and must later be evaluated against a broader labeled question set.

## Safety behavior

An empty or below-threshold result is not a system failure. It routes to: `I do not have sufficient information in Lenny's Podcast archive to answer this.` The model will not be asked to fill the evidence gap with general knowledge.

