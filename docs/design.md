# Design Specification

The desktop UI uses a two-pane layout: a dominant chat workspace on the left and an artifact viewer on the right. Header controls expose the active provider and output mode so users understand which model and skill they are using.

Chat messages visually distinguish user input from assistant output. Citations are collapsed beneath an answer to keep the response scannable while keeping evidence one click away. Empty state includes a realistic starter prompt. The Send action is disabled until a session exists and displays “Thinking…” during a request.

On screens below 850px, the layout stacks chat above the artifact viewer; no functionality is hidden. Labels, contrast, native form controls, semantic headings, keyboard Enter-to-send behavior, and descriptive iframe titles provide a usable baseline for keyboard and assistive-technology users.

Artifact preview accepts Markdown or HTML. Markdown renders as readable document content. HTML is sanitized and placed in a sandboxed frame, intentionally choosing safety over support for scripts, forms, external frames, and parent-page integration.
