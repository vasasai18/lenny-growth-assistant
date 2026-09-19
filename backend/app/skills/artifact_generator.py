import re
from dataclasses import dataclass
from typing import Literal

import bleach
from bleach.css_sanitizer import CSSSanitizer


ArtifactKind = Literal["markdown", "html"]


@dataclass(frozen=True)
class ArtifactDraft:
    artifact_type: ArtifactKind
    content: str
    blocked_content: bool = False


ALLOWED_TAGS = {
    "html", "head", "body", "title", "style", "main", "header", "footer",
    "section", "article", "aside", "nav", "div", "span", "p", "h1", "h2",
    "h3", "h4", "ul", "ol", "li", "blockquote", "pre", "code", "strong",
    "em", "small", "br", "hr", "table", "thead", "tbody", "tr", "th", "td",
    "a", "figure", "figcaption",
}
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "aria-label", "aria-describedby", "role"],
    "a": ["href", "title", "target", "rel"],
    "th": ["scope", "colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
}


def strip_code_fence(content: str) -> str:
    match = re.fullmatch(r"\s*```(?:html|markdown|md)?\s*(.*?)\s*```\s*", content, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else content.strip()


def sanitize_html(content: str, max_chars: int = 100_000) -> ArtifactDraft:
    if len(content) > max_chars:
        raise ValueError(f"HTML artifact exceeds the {max_chars}-character limit.")
    original = strip_code_fence(content)
    without_dangerous_blocks = re.sub(
        r"<\s*(script|iframe|object|embed|form|svg|math)\b[^>]*>.*?<\s*/\s*\1\s*>",
        "",
        original,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # CSS URLs and imports can make network requests even when scripts are blocked.
    no_remote_css = re.sub(r"@import\s+[^;]+;?", "", without_dangerous_blocks, flags=re.IGNORECASE)
    no_remote_css = re.sub(r"url\s*\([^)]*\)", "none", no_remote_css, flags=re.IGNORECASE)
    css = CSSSanitizer(
        allowed_css_properties=[
            "background", "background-color", "border", "border-color", "border-radius",
            "border-style", "border-width", "box-shadow", "color", "display", "flex",
            "flex-direction", "flex-wrap", "font-family", "font-size", "font-style",
            "font-weight", "gap", "grid-template-columns", "height", "justify-content",
            "line-height", "margin", "margin-bottom", "margin-left", "margin-right",
            "margin-top", "max-width", "min-height", "opacity", "overflow", "padding",
            "padding-bottom", "padding-left", "padding-right", "padding-top", "text-align",
            "text-decoration", "width",
        ]
    )
    clean = bleach.clean(
        no_remote_css,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        css_sanitizer=css,
        strip=True,
        strip_comments=True,
    )
    # Links may open a new tab, but cannot control the opener.
    clean = re.sub(
        r'<a\s+([^>]*href="https?://[^">]+"[^>]*)>',
        lambda match: '<a ' + re.sub(r'\s+(?:target|rel)="[^"]*"', '', match.group(1)) + ' target="_blank" rel="noopener noreferrer">',
        clean,
        flags=re.IGNORECASE,
    )
    return ArtifactDraft("html", clean, blocked_content=clean != original)


def prepare_markdown(content: str, max_chars: int = 100_000) -> ArtifactDraft:
    clean = strip_code_fence(content)
    if len(clean) > max_chars:
        raise ValueError(f"Markdown artifact exceeds the {max_chars}-character limit.")
    # Raw HTML is unnecessary because react-markdown is configured not to render it.
    blocked = bool(re.search(r"<\s*(script|iframe|object|embed|form|style)\b", clean, re.IGNORECASE))
    clean = re.sub(
        r"<\s*(script|iframe|object|embed|form|style)\b[^>]*>.*?<\s*/\s*\1\s*>",
        "",
        clean,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return ArtifactDraft("markdown", clean, blocked_content=blocked)


def prepare_artifact(kind: ArtifactKind, content: str, max_chars: int = 100_000) -> ArtifactDraft:
    return sanitize_html(content, max_chars) if kind == "html" else prepare_markdown(content, max_chars)
