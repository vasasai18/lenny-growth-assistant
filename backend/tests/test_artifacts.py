import pytest

from app.skills.artifact_generator import prepare_markdown, sanitize_html


def test_html_sanitizer_removes_executable_and_remote_content() -> None:
    draft = sanitize_html(
        '<main onclick="steal()"><h1>Safe</h1><script>alert(1)</script>'
        '<iframe src="https://evil.test"></iframe><img src="https://evil.test/x">'
        '<style>.x{background:url(https://evil.test/x)}</style></main>'
    )

    lowered = draft.content.lower()
    assert "safe" in lowered
    assert "alert(1)" not in lowered
    assert "script" not in lowered
    assert "iframe" not in lowered
    assert "onclick" not in lowered
    assert "evil.test" not in lowered
    assert draft.blocked_content


def test_markdown_removes_dangerous_raw_blocks() -> None:
    draft = prepare_markdown("# Memo\n\n<script>alert(1)</script>\n\nUseful text.")

    assert draft.content == "# Memo\n\n\n\nUseful text."
    assert draft.blocked_content


def test_artifact_size_limit() -> None:
    with pytest.raises(ValueError, match="character limit"):
        sanitize_html("x" * 11, max_chars=10)
