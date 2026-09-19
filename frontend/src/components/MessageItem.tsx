import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "../lib/api";

export function MessageItem({ message, onArtifact }: { message: Message; onArtifact: (id: string) => void }) {
  return <article className={`message ${message.role}`} aria-label={`${message.role} message`}>
    <div className="flex items-center justify-between gap-3"><span className="eyebrow">{message.role === "assistant" ? "Lenny Assistant" : "You"}</span>{message.provider && <span className="badge">{message.provider === "ollama" ? "Local Ollama" : "Cloud Anthropic"}</span>}</div>
    <div className="prose"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown></div>
    {!!message.sources?.length && <details className="sources"><summary>{message.sources.length} transcript source{message.sources.length === 1 ? "" : "s"}</summary><ol>{message.sources.map((source) => <li key={`${message.id}-${source.citation_number}`}><a href={source.source_url} target="_blank" rel="noopener noreferrer">[{source.citation_number}] {source.episode_title}</a><span>{source.guest_name ?? "Guest unavailable"} · {source.timestamp_ref ?? "Timestamp unavailable"}</span></li>)}</ol></details>}
    {message.artifacts?.map((artifact) => <button className="secondary mt-3" key={artifact.id} onClick={() => onArtifact(artifact.id)}>Open {artifact.artifact_type.toUpperCase()} artifact</button>)}
  </article>;
}
