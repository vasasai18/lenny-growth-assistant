# Agent Transcript 10: Artifacts and Frontend

## Decisions

- Artifact modes remain explicit API values so the model does not infer hidden intent.
- HTML is sanitized on the backend before persistence and again with DOMPurify before preview.
- The iframe has an empty `sandbox`; no scripts, forms, same-origin access, popups, or navigation permissions are granted.
- A restrictive iframe CSP blocks all network access and permits only inline CSS and data images.
- Markdown uses `react-markdown` and `remark-gfm` without a raw-HTML plugin.
- The interface favors evidence visibility, clear provider state, keyboard focus, and responsive behavior over animation.

## Verification

Backend artifact tests cover executable tags, event handlers, remote CSS/resources, raw Markdown blocks, and size limits. Frontend tests inspect the sanitized iframe document and CSP.
