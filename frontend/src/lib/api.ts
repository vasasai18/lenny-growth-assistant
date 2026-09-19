export type Provider = "ollama" | "anthropic";
export type Mode = "answer" | "ship30" | "markdown" | "html";

export interface Source {
  citation_number: number;
  episode_title: string;
  guest_name?: string | null;
  publication_date?: string | null;
  timestamp_ref?: string | null;
  source_url: string;
  similarity: number;
}
export interface Artifact { id: string; message_id: string; artifact_type: "markdown" | "html"; title: string; content: string; created_at: string }
export interface Message { id: string; session_id: string; role: "user" | "assistant"; content: string; provider?: string | null; mode?: string | null; sources: Source[]; created_at: string; artifacts: Artifact[] }
export interface SessionSummary { id: string; title: string; created_at: string; updated_at: string }
export interface Session extends SessionSummary { user_metadata: Record<string, unknown>; messages: Message[] }
export interface ChatResponse { session_id: string; message: Message; provider: Provider; model: string; artifact?: Artifact | null }

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init?.headers } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.error?.message ?? `Request failed (${response.status})`);
  return body as T;
}

export const api = {
  listSessions: () => request<SessionSummary[]>("/api/sessions"),
  createSession: () => request<SessionSummary>("/api/sessions", { method: "POST", body: JSON.stringify({ title: "New chat" }) }),
  getSession: (id: string) => request<Session>(`/api/sessions/${id}`),
  chat: (sessionId: string, message: string, provider: Provider, mode: Mode) => request<ChatResponse>("/api/chat", { method: "POST", body: JSON.stringify({ session_id: sessionId, message, provider, mode }) }),
};
