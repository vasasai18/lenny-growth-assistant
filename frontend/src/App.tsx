import { useCallback, useEffect, useMemo, useState } from "react";
import { ArtifactViewer } from "./components/ArtifactViewer";
import { ChatPane } from "./components/ChatPane";
import { SessionSidebar } from "./components/SessionSidebar";
import { useChatStream } from "./hooks/useChatStream";
import { api, Artifact, Mode, Provider, Session, SessionSummary } from "./lib/api";

export default function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]); const [session, setSession] = useState<Session | null>(null);
  const [provider, setProvider] = useState<Provider>((import.meta.env.VITE_DEFAULT_PROVIDER as Provider) || "ollama"); const [mode, setMode] = useState<Mode>("answer"); const [artifact, setArtifact] = useState<Artifact | null>(null); const [error, setError] = useState("");
  const { send, loading, status } = useChatStream();
  const refreshSessions = useCallback(async () => setSessions(await api.listSessions()), []);
  const selectSession = useCallback(async (id: string) => { setError(""); setArtifact(null); try { setSession(await api.getSession(id)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load this chat."); } }, []);
  const newSession = useCallback(async () => { try { const created = await api.createSession(); await refreshSessions(); await selectSession(created.id); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create a chat."); } }, [refreshSessions, selectSession]);
  useEffect(() => { void (async () => { try { const listed = await api.listSessions(); setSessions(listed); if (listed[0]) await selectSession(listed[0].id); else await newSession(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not connect to the API."); } })(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const artifacts = useMemo(() => session?.messages.flatMap((message) => message.artifacts ?? []) ?? [], [session]);
  const openArtifact = (id: string) => setArtifact(artifacts.find((item) => item.id === id) ?? null);
  const handleSend = async (text: string) => { if (!session) return; setError(""); try { const result = await send(session.id, text, provider, mode); await Promise.all([selectSession(session.id), refreshSessions()]); if (result.artifact) setArtifact(result.artifact); } catch (reason) { setError(reason instanceof Error ? reason.message : "The request failed."); throw reason; } };
  return <div className={`app-shell ${artifact ? "with-artifact" : ""}`}><SessionSidebar sessions={sessions} activeId={session?.id} onSelect={(id) => void selectSession(id)} onNew={() => void newSession()} /><div className="workspace">{error && <div className="error" role="alert">{error}</div>}<ChatPane messages={session?.messages ?? []} provider={provider} mode={mode} loading={loading} status={status} onProvider={setProvider} onMode={setMode} onSend={handleSend} onArtifact={openArtifact} /></div><ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} /></div>;
}
