import { FormEvent, useState } from "react";
import { Message, Mode, Provider } from "../lib/api";
import { MessageItem } from "./MessageItem";
import { ModelSelector } from "./ModelSelector";

const modes: { value: Mode; label: string }[] = [{ value: "answer", label: "Answer" }, { value: "ship30", label: "Ship 30" }, { value: "markdown", label: "Markdown" }, { value: "html", label: "HTML/CSS" }];

export function ChatPane({ messages, provider, mode, loading, status, onProvider, onMode, onSend, onArtifact }: { messages: Message[]; provider: Provider; mode: Mode; loading: boolean; status: string; onProvider: (value: Provider) => void; onMode: (value: Mode) => void; onSend: (value: string) => Promise<void>; onArtifact: (id: string) => void }) {
  const [text, setText] = useState("");
  const submit = async (event: FormEvent) => { event.preventDefault(); const value = text.trim(); if (!value || loading) return; setText(""); try { await onSend(value); } catch { setText(value); } };
  return <main className="chat-pane">
    <header className="chat-header"><div><p className="eyebrow">Transcript-grounded guidance</p><h2 className="text-lg font-bold">Ask Lenny’s archive</h2></div><ModelSelector value={provider} onChange={onProvider} /></header>
    <section className="messages" aria-live="polite">{!messages.length && <div className="empty"><span>✦</span><h2>What product decision are you working through?</h2><p>Ask about onboarding, growth, strategy, hiring, or another topic covered in Lenny’s Podcast.</p></div>}{messages.map((message) => <MessageItem key={message.id} message={message} onArtifact={onArtifact} />)}{loading && <div className="loading" role="status"><span className="pulse" />{status}</div>}</section>
    <form className="composer" onSubmit={submit}><div className="mode-row" aria-label="Response mode">{modes.map((item) => <button type="button" key={item.value} className={mode === item.value ? "active" : ""} aria-pressed={mode === item.value} onClick={() => onMode(item.value)}>{item.label}</button>)}</div><label className="sr-only" htmlFor="question">Your question</label><textarea id="question" value={text} onChange={(event) => setText(event.target.value)} placeholder="Ask a product or growth question…" rows={3} maxLength={10000} /><div className="composer-footer"><span>{provider === "ollama" ? "Private · runs locally" : "Sends context to Anthropic"}</span><button className="primary" disabled={loading || !text.trim()}>{loading ? "Working…" : "Send"}</button></div></form>
  </main>;
}
