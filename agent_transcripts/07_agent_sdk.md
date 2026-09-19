# Agent Transcript 07: Required Agent SDK

## Goal

Use the official Anthropic Claude Agent SDK for the cloud agent and expose retrieval, Ship 30, Markdown, and HTML capabilities through explicit tools.

## SDK integration

- Package: `claude-agent-sdk==0.2.157`.
- Custom tools run as an in-process SDK MCP server named `lenny`.
- The cloud runner invokes the SDK `query()` loop with a strict system prompt.
- Maximum agent turns: 8.
- Maximum per-request SDK budget: USD 0.50.
- Application session history remains in PostgreSQL; the SDK session ID is recorded as response metadata for diagnostics.

## Tool boundaries

1. `search_transcripts(query, top_k)` embeds the query and returns thresholded evidence plus citation metadata.
2. `generate_ship30_essay(topic)` returns evidence and the dedicated 1,250-word writing contract.
3. `create_markdown_artifact(instructions, research_query)` returns evidence and a Markdown-only artifact contract.
4. `create_html_artifact(instructions, research_query)` returns evidence and a no-script, no-network HTML/CSS contract.

The final Ship 30 and artifact validators are implemented in their dedicated later phases; the agent-facing contracts already exist here.

## Security boundary

Only the four `mcp__lenny__*` tools are supplied and allowed. Bash, filesystem reading/writing, globbing, grep, web search/fetch, editing, and subagents are explicitly disallowed. Project, local, and user SDK settings are not loaded. Transcript content is marked as untrusted quoted data and cannot grant new permissions.

## Local route

The 3B Ollama model does not autonomously choose tools. The application deterministically retrieves evidence before generation and selects the dedicated mode contract from the user's explicit action. This makes the local demo more reliable while keeping the same retrieval and citation boundary.

## Failure handling

- Empty/weak retrieval returns the exact insufficient-information response without model generation.
- Missing Anthropic configuration fails before starting the SDK process.
- SDK error results and empty responses become typed provider errors.
- Tool failures remain visible and do not enable another tool or provider automatically.

