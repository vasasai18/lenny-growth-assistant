import { Provider } from "../lib/api";

export function ModelSelector({ value, onChange }: { value: Provider; onChange: (value: Provider) => void }) {
  return <label className="flex items-center gap-2 text-sm font-medium">Provider
    <select aria-label="LLM provider" className="rounded-lg border border-stone-300 bg-white px-3 py-2" value={value} onChange={(event) => onChange(event.target.value as Provider)}>
      <option value="ollama">Local — Ollama</option><option value="anthropic">Cloud — Anthropic</option>
    </select>
  </label>;
}
