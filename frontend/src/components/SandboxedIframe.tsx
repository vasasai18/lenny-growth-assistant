import DOMPurify from "dompurify";

export function buildSafeDocument(html: string): string {
  const sanitized = DOMPurify.sanitize(html, {
    FORBID_TAGS: ["script", "iframe", "object", "embed", "form", "base", "link", "meta", "svg", "math"],
    FORBID_ATTR: ["src", "srcset", "onerror", "onclick", "onload", "formaction"],
  });
  const csp = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src 'none'; connect-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'";
  return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${csp}"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>${sanitized}</body></html>`;
}

export function SandboxedIframe({ html, title }: { html: string; title: string }) {
  return <iframe className="h-full min-h-[520px] w-full rounded-lg border-0 bg-white" title={title} sandbox="" referrerPolicy="no-referrer" srcDoc={buildSafeDocument(html)} />;
}
