# 2–3 Minute Demo Script

## 0:00–0:20 — Problem

“Product and growth teams learn a lot from Lenny’s Podcast, but searching dozens of long transcripts is slow. The Lenny Growth Assistant turns that archive into a conversational, evidence-first workspace.”

Show the session sidebar, provider selector, and empty chat.

## 0:20–0:55 — Grounded question and citations

Select **Local — Ollama** and ask: “How should a product team decide what to build when evidence is limited?”

“The question is embedded locally, compared with transcript chunks in pgvector, and only sufficiently relevant passages are sent to the model. The answer includes numbered episode citations rather than pretending general model knowledge came from the archive.”

Expand one source and point out the episode, guest, timestamp, and original URL.

## 0:55–1:15 — Follow-up and persistence

Ask: “Turn those ideas into a three-step experiment for an onboarding problem.”

“Follow-ups receive recent history from this session. A new chat creates a separate database session, so histories cannot leak into each other.”

Create a new chat briefly, then return to the first session.

## 1:15–1:45 — Ship 30

Choose **Ship 30** and ask for an essay about running small product experiments.

“Ship 30 is a dedicated reusable skill, not a sentence in the normal prompt. It targets about 1,250 words, validates structure and citations, and removes quotations that are not present in retrieved transcript evidence.”

## 1:45–2:15 — Artifacts and security

Choose **Markdown** and generate a decision memo. Open Preview and Source.

Then show an HTML/CSS artifact.

“Generated HTML is untrusted. The backend removes dangerous content, the browser sanitizes again with DOMPurify, and the result runs in an iframe with an empty sandbox and network-blocking Content Security Policy.”

## 2:15–2:40 — Provider switching and trade-off

Point to **Local — Ollama** and **Cloud — Anthropic**.

“Provider selection is runtime and per request. There is no silent fallback, so local content is never unexpectedly sent to the cloud. The trade-off is that the 3B local model is private and inexpensive but slower and weaker for long-form work; Anthropic is stronger but requires a key and sends relevant context externally.”

End on `/api/health` or the application with source cards visible.
