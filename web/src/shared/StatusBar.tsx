// Header pill: is monitoring live, when did it last update, and an "Update now" action.
import { useState } from "react";
import { api } from "../api/client";
import { useApi } from "./useApi";

export function StatusBar({ onChanged }: { onChanged: () => void }) {
  const overview = useApi(api.overview);
  const monitor = useApi(api.monitor);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const o = overview.data;
  const demo = o?.profile === "demo";
  const empty = demo && (o?.articles ?? 0) === 0;

  const act = async (run: () => Promise<unknown>) => {
    setBusy(true);
    setNote(null);
    try { await run(); onChanged(); } catch (e) { setNote((e as Error).message); }
    finally { setBusy(false); overview.reload(); monitor.reload(); }
  };

  const last = monitor.data?.last_round_at;
  return (
    <div className="status">
      <span className={`dot ${demo ? "demo" : "live"}`} />
      <span className="status-text">
        {demo ? "Demo data (fictional companies)" : `Reading ${o?.outlets_enabled ?? "…"} news sources`}
        {last && ` · last checked ${new Date(last).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`}
      </span>
      {empty ? (
        <button className="small primary" disabled={busy} onClick={() => act(api.loadDemo)}>{busy ? "Loading…" : "Load demo"}</button>
      ) : (
        <button className="small" disabled={busy || !o} onClick={() => act(api.runRound)} title="Read the latest news, update events and re-check stock reactions">
          {busy ? "Checking…" : "Check for news"}
        </button>
      )}
      {note && <span className="status-note">{note}</span>}
    </div>
  );
}
