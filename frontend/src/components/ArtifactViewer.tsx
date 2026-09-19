import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Artifact } from "../lib/api";
import { SandboxedIframe } from "./SandboxedIframe";

export function ArtifactViewer({ artifact, onClose }: { artifact: Artifact | null; onClose: () => void }) {
  const [tab, setTab] = useState<"preview" | "source">("preview");
  if (!artifact) return null;
  return <aside className="artifact-panel" aria-label="Artifact viewer">
    <header className="artifact-header"><div><p className="eyebrow">{artifact.artifact_type} artifact</p><h2 className="font-bold">{artifact.title}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close artifact">×</button></header>
    <div className="tabs" role="tablist"><button className={tab === "preview" ? "active" : ""} onClick={() => setTab("preview")}>Preview</button><button className={tab === "source" ? "active" : ""} onClick={() => setTab("source")}>Source</button><button onClick={() => navigator.clipboard.writeText(artifact.content)}>Copy</button></div>
    <div className="artifact-body">{tab === "source" ? <pre className="source-code"><code>{artifact.content}</code></pre> : artifact.artifact_type === "html" ? <SandboxedIframe html={artifact.content} title={artifact.title} /> : <div className="prose artifact-markdown"><ReactMarkdown remarkPlugins={[remarkGfm]}>{artifact.content}</ReactMarkdown></div>}</div>
  </aside>;
}
