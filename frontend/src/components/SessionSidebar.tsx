import { SessionSummary } from "../lib/api";

export function SessionSidebar({ sessions, activeId, onSelect, onNew }: { sessions: SessionSummary[]; activeId?: string; onSelect: (id: string) => void; onNew: () => void }) {
  return <aside className="sidebar" aria-label="Chat sessions">
    <div><p className="eyebrow">Oogway Labs</p><h1 className="text-xl font-bold">Lenny Growth Assistant</h1></div>
    <button className="primary w-full" onClick={onNew}>＋ New chat</button>
    <nav className="space-y-1 overflow-y-auto" aria-label="Previous sessions">
      {sessions.map((session) => <button key={session.id} className={`session ${activeId === session.id ? "active" : ""}`} onClick={() => onSelect(session.id)}>{session.title}</button>)}
      {!sessions.length && <p className="text-sm text-stone-500">No chats yet.</p>}
    </nav>
  </aside>;
}
