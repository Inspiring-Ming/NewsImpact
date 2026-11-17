// "My companies": the tickers a person stars. For a signed-in person the list is
// kept on the server, because alerts (e.g. Discord) are sent for those companies and they are
// always followed. In a public demo, visitors keep their stars in their own browser only, so
// they change nothing for anyone else (ADR 0037).
import { useEffect, useState } from "react";
import { api } from "../api/client";

const KEY = "newsimpact-starred"; // per-browser convenience; may be unavailable (private mode)

function local(): Set<string> {
  try { return new Set(JSON.parse(localStorage.getItem(KEY) ?? "[]") as string[]); } catch { return new Set(); }
}

export function useStarred() {
  const [starred, setStarred] = useState<Set<string>>(new Set());
  const [onServer, setOnServer] = useState(false);
  useEffect(() => {
    api.me().then((m) => {
      setOnServer(!m.guest);
      if (!m.guest) api.watchlist().then((t) => setStarred(new Set(t))).catch(() => undefined);
      else setStarred(local());
    }).catch(() => setStarred(local()));
  }, []);
  const toggle = (ticker: string) => {
    const follow = !starred.has(ticker);
    const next = new Set(starred);
    if (follow) next.add(ticker); else next.delete(ticker);
    setStarred(next); // show it at once
    if (!onServer) {
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch { /* storage blocked: this visit only */ }
      return;
    }
    (follow ? api.follow(ticker) : api.unfollow(ticker)).then((t) => setStarred(new Set(t))).catch(() => setStarred(starred));
  };
  return { starred, toggle };
}
