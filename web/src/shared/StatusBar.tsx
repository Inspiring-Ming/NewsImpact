// Header pill: is monitoring live, when did it last update, and (for the owner) "Update now".
// In a public demo, visitors see the status only: updates run on the schedule.
import { useState } from "react";
import { api } from "../api/client";
import { useApi } from "./useApi";

export function StatusBar({ onChanged }: { onChanged: () => void }) {
  const overview = useApi(api.overview);
  const monitor = useApi(api.monitor);
  const me = useApi(api.me);
  const owner = me.data?.admin ?? false;
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
        {demo ? "Demo data (fictional companies)" : "Live"}
        {last && ` · updated ${new Date(last).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`}
        {!demo && o?.monitor_every_minutes ? ` · updates every ${o.monitor_every_minutes} min` : ""}
      </span>
      {!owner ? null : empty ? (
        <button className="small primary" disabled={busy} onClick={() => act(api.loadDemo)}>{busy ? "Loading…" : "Load demo"}</button>
      ) : (
        <button className="small" disabled={busy || !o} onClick={() => act(api.runRound)} title="Fetch the latest news now, update events and re-measure stock moves. Can take a few minutes.">
          {busy ? "Updating… (a few minutes)" : "Update now"}
        </button>
      )}
      {note && <span className="status-note">{note}</span>}
    </div>
  );
}
