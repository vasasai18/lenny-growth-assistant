# Product Design: The Lenny Growth Assistant

## 1. Design goal

The interface should make evidence feel central, not decorative. A beginner should understand what to do immediately, while an evaluator should be able to see the selected model, inspect sources, create an artifact, and test independent sessions without hunting through settings.

## 2. UI principles

- Evidence first: citations sit directly below the answer they support.
- Visible system state: provider, mode, retrieval, generation, success, and failure states are named plainly.
- Progressive disclosure: source details and advanced artifact controls stay collapsed until needed.
- Safe by default: HTML preview is isolated; raw source is available separately for inspection.
- Calm over flashy: high contrast, readable typography, restrained motion, and no unnecessary effects.
- Keyboard and screen-reader usable: semantic controls, focus states, labels, live regions, and logical order.

## 3. Information architecture

- Session sidebar
  - Product name
  - New Chat button
  - Previous sessions
- Conversation workspace
  - Session title
  - Provider selector and current-provider badge
  - Message history with source cards
  - Mode/action controls
  - Composer and send/stop button
- Artifact workspace
  - Artifact title and type
  - Preview/source tabs
  - Copy/download actions
  - Close/collapse action

## 4. Desktop layout

The application uses three functional regions:

1. A narrow left session sidebar.
2. A flexible central chat pane.
3. A right artifact panel that opens only when an artifact exists or the user selects one.

The chat remains usable when the artifact panel is open. A draggable divider is optional; fixed responsive widths are sufficient for the assessment.

```text
+----------------+--------------------------------+--------------------------+
| Sessions       | Chat                           | Artifact                 |
|                | [Local: llama3.2:3b]           | Preview | Source         |
| + New Chat     |                                |                          |
|                | User question                  | Rendered output          |
| Previous chats | Assistant answer               |                          |
|                | Sources: Episode A, Episode B  |                          |
|                |                                |                          |
|                | [Ask...] [Send]                |                          |
+----------------+--------------------------------+--------------------------+
```

## 5. Mobile layout

- The session sidebar becomes a modal drawer opened from the top bar.
- Chat is the default full-width view.
- The artifact viewer becomes a full-screen sheet with a clear Back to chat control.
- Provider and mode controls wrap without horizontal scrolling.
- The composer remains visible above the safe-area inset.

## 6. Component hierarchy

```text
App
├── SessionSidebar
│   ├── NewChatButton
│   └── SessionList
├── ChatPane
│   ├── ChatHeader
│   │   ├── ModelSelector
│   │   └── ProviderBadge
│   ├── MessageList
│   │   └── MessageItem
│   │       └── SourceList
│   ├── ModeSelector
│   └── ChatComposer
└── ArtifactViewer
    ├── ArtifactToolbar
    ├── MarkdownPreview
    └── SandboxedIframe
```

## 7. Core interactions

### New chat

The New Chat button creates a server-side session immediately and moves focus to the composer. The empty state provides three example grounded questions without automatically sending them.

### Provider selection

The selector contains `Local — Ollama` and `Cloud — Anthropic`. The current provider is repeated as a badge near the response. Selecting cloud for the first time shows a short disclosure that relevant messages and transcript excerpts will be sent to Anthropic.

### Modes

The default mode is Answer. Additional explicit actions are Ship 30, Markdown artifact, and HTML artifact. The chosen mode appears above the composer and is included in the request; it does not depend on the model guessing from hidden syntax.

### Citations

Each assistant response has a Sources section containing numbered cards. A collapsed card shows episode and guest. Expanding it shows timestamp/section, a short supporting excerpt, and source link. Citation numbers in the response map to these cards.

### Artifact viewer

Creating or selecting an artifact opens the right panel. Preview is the default. Source shows copyable generated Markdown or HTML. HTML preview receives sanitized `srcdoc` inside the sandboxed iframe; it is not injected into the application DOM.

## 8. Loading states

- `Searching transcripts…` while embedding and retrieval run.
- `Found N relevant passages` after successful retrieval.
- `Writing with Local Ollama…` or `Writing with Cloud Anthropic…` during generation.
- A streaming caret while tokens arrive.
- Skeleton rows while session history loads.
- Buttons disable only when repeating the action would be unsafe; Stop remains available during generation when supported.

Status text uses an `aria-live="polite"` region and does not rely only on animation or color.

## 9. Empty states

- No sessions: explain New Chat in one sentence.
- New conversation: show example product/growth questions.
- No artifact selected: explain that Ship 30, Markdown, or HTML actions open the panel.
- No sufficient evidence: show the standard refusal plus a suggestion to rephrase within product/growth topics; do not fabricate recommended sources.

## 10. Error states

Errors use simple language, retain the user's draft, and provide the next action.

- Ollama stopped: `Local Ollama is not reachable. Start Ollama, then retry, or choose Cloud.`
- Cloud key missing: `Cloud mode is not configured. Add ANTHROPIC_API_KEY on the server or choose Local.`
- Database unavailable: `Chats cannot be loaded or saved right now. Check the database service.`
- Timeout: `The model took too long to respond. Your message is saved; retry it.`
- Unsafe artifact: `This artifact contained blocked content and was not previewed.`

Technical details and request IDs can be expanded for troubleshooting without overwhelming the default view.

## 11. Visual system

- Neutral background with one restrained accent color.
- Minimum 16 px body text and comfortable line height.
- Chat content has a readable maximum line length of about 75 characters.
- Source cards are visually distinct but secondary to the answer.
- Provider badges use text and an icon in addition to color.
- Focus rings are always visible for keyboard users.
- Motion respects `prefers-reduced-motion`.

## 12. Accessibility

- Meet WCAG AA contrast for text and interactive controls.
- Use buttons for actions and links for navigation; avoid clickable generic containers.
- Associate every input with a visible or programmatic label.
- Preserve a logical heading hierarchy and DOM order.
- Provide keyboard access to sidebar, provider selector, messages, source disclosures, artifact tabs, and composer.
- Move focus predictably when opening/closing the mobile artifact sheet.
- Announce loading, completion, and errors without repeatedly announcing streamed token fragments.
- Give icons accessible names and hide purely decorative graphics.

## 13. Responsive breakpoints

- At wide desktop sizes, show sessions, chat, and artifact panels together.
- At medium widths, collapse the session sidebar first and keep chat plus artifact side-by-side.
- At phone widths, use one primary view at a time with drawer/sheet navigation.

Exact pixel breakpoints will follow content fit rather than device names and will be verified manually at 375 px, 768 px, 1024 px, and 1440 px widths.

## 14. UX decisions and trade-offs

- Explicit modes are clearer and more testable than asking the model to infer whether the user wants an essay or artifact.
- Provider switching is per request, not a hidden global setting, so screenshots and persisted messages can show what generated each response.
- Source excerpts are collapsed to preserve readability but remain one action away.
- HTML scripts are blocked. This excludes interactive JavaScript artifacts, but it materially reduces risk and still satisfies HTML/CSS rendering.
- Streaming is desirable but not allowed to complicate correct persistence. The final server result remains the authoritative saved message.

