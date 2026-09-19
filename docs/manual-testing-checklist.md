# Manual UI Testing Checklist

Run the application at `http://localhost:5173`, then record pass/fail for each item.

## Core flow

- [ ] New Chat creates a blank, independent session.
- [ ] A grounded product question returns an answer with at least one source.
- [ ] Source links show episode, guest, and timestamp when available.
- [ ] A follow-up uses the current session context.
- [ ] A second session does not show messages from the first.
- [ ] Reloading the page preserves both sessions and their messages.

## Providers and failures

- [ ] Local Ollama is visibly selected and produces a response.
- [ ] Cloud Anthropic can be selected when `ANTHROPIC_API_KEY` is configured.
- [ ] Stopping Ollama produces a useful error without losing the typed question.
- [ ] Selecting unconfigured Anthropic produces a useful configuration error.

## Writing and artifacts

- [ ] Ship 30 mode produces roughly 1,250 words with headings, bullets, and citations.
- [ ] Markdown mode opens a rendered artifact and its source tab.
- [ ] HTML/CSS mode opens inside the sandboxed iframe.
- [ ] HTML scripts, forms, event handlers, iframes, and remote resources do not execute/load.
- [ ] Copy artifact copies the source.
- [ ] Closing and reopening an artifact works.

## Accessibility and responsiveness

- [ ] All controls are reachable with Tab and have a visible focus ring.
- [ ] Provider and mode controls have accessible labels/state.
- [ ] Loading and errors are announced by assistive technology.
- [ ] Layout works at 375, 768, 1024, and 1440 px widths.
- [ ] Reduced-motion preference disables the loading animation.
