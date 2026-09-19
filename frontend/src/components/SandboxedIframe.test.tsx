import { describe, expect, it } from "vitest";
import { buildSafeDocument } from "./SandboxedIframe";

describe("buildSafeDocument", () => {
  it("removes scripts, handlers, remote images, and embeds a restrictive CSP", () => {
    const document = buildSafeDocument('<h1 onclick="bad()">Safe</h1><script>alert(1)</script><img src="https://evil.test/x">');
    expect(document).toContain("Safe");
    expect(document).not.toContain("onclick");
    expect(document).not.toContain("<script");
    expect(document).not.toContain("evil.test");
    expect(document).toContain("default-src 'none'");
  });
});
