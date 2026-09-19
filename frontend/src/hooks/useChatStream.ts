import { useState } from "react";
import { api, Mode, Provider } from "../lib/api";

export function useChatStream() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const send = async (sessionId: string, text: string, provider: Provider, mode: Mode) => {
    setLoading(true);
    setStatus(mode === "answer" ? "Searching transcripts and writing…" : mode === "ship30" ? "Writing a grounded Ship 30 essay…" : "Creating a grounded artifact…");
    try { return await api.chat(sessionId, text, provider, mode); }
    finally { setLoading(false); setStatus(""); }
  };
  return { send, loading, status };
}
