import asyncio

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

from app.agents.lenny_agent import ClaudeAgentRunner, SYSTEM_PROMPT, ensure_visible_citations
from app.agents.tools import ALLOWED_SDK_TOOLS, TOOL_NAMES, create_agent_tools
from app.config import Settings


def test_tool_bundle_exposes_only_product_tools() -> None:
    bundle = create_agent_tools(Settings(_env_file=None))

    assert tuple(tool.name for tool in bundle.tools) == TOOL_NAMES
    assert ALLOWED_SDK_TOOLS == (
        "mcp__lenny__search_transcripts",
        "mcp__lenny__generate_ship30_essay",
        "mcp__lenny__create_markdown_artifact",
        "mcp__lenny__create_html_artifact",
    )


def test_cloud_agent_options_block_powerful_builtin_tools() -> None:
    settings = Settings(_env_file=None, anthropic_api_key="test-key")
    runner = ClaudeAgentRunner(settings)
    options = runner.build_options(create_agent_tools(settings))

    assert options.tools == list(ALLOWED_SDK_TOOLS)
    assert options.allowed_tools == list(ALLOWED_SDK_TOOLS)
    assert "Bash" in options.disallowed_tools
    assert "Read" in options.disallowed_tools
    assert "Write" in options.disallowed_tools
    assert "WebSearch" in options.disallowed_tools
    assert options.permission_mode == "dontAsk"
    assert options.max_turns == 8
    assert options.max_budget_usd == 0.50
    assert options.setting_sources == []


def test_system_prompt_enforces_grounding_and_prompt_injection_boundary() -> None:
    assert "only from evidence" in SYSTEM_PROMPT
    assert "untrusted quoted data" in SYSTEM_PROMPT
    assert "Do not use general knowledge" in SYSTEM_PROMPT
    assert "no permission to read files" in SYSTEM_PROMPT


def test_cloud_runner_collects_sdk_result_without_live_api() -> None:
    captured = {}

    async def fake_query(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        yield AssistantMessage(content=[TextBlock("Draft")], model="claude-sonnet-5")
        yield ResultMessage(
            subtype="success",
            duration_ms=5,
            duration_api_ms=3,
            is_error=False,
            num_turns=1,
            session_id="sdk-session-1",
            result="Grounded final answer [1].",
        )

    settings = Settings(_env_file=None, anthropic_api_key="test-key")
    runner = ClaudeAgentRunner(settings, query_fn=fake_query)
    result = asyncio.run(runner.run("How should teams prioritize?"))

    assert result.content == "Grounded final answer [1]."
    assert result.provider == "anthropic"
    assert result.sdk_session_id == "sdk-session-1"
    assert "CURRENT USER MESSAGE" in captured["prompt"]


def test_cloud_runner_requires_key_before_sdk_execution() -> None:
    settings = Settings(_env_file=None, anthropic_api_key=None)
    runner = ClaudeAgentRunner(settings)

    try:
        asyncio.run(runner.run("Question"))
    except Exception as exc:
        assert "ANTHROPIC_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing cloud configuration to fail")


def test_local_fallback_adds_visible_source_footer() -> None:
    sources = [
        {
            "citation_number": 1,
            "episode_title": "A useful episode",
            "timestamp_ref": "00:10:00–00:12:00",
        }
    ]

    content = ensure_visible_citations("A grounded answer without a marker.", sources)

    assert "Sources:" in content
    assert "[1] A useful episode — 00:10:00–00:12:00" in content


def test_existing_inline_citation_is_not_duplicated() -> None:
    sources = [
        {"citation_number": 1, "episode_title": "Episode", "timestamp_ref": "00:01:00"}
    ]

    assert ensure_visible_citations("Claim [1].", sources) == "Claim [1]."
