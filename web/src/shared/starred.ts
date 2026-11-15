// "My companies": the tickers a visitor follows, kept in this browser only (a per-viewer
// convenience until accounts exist). Storage can be unavailable (private mode), so every
// access is guarded and the page works without it.
import { useState } from "react";

const KEY = "newsimpact.starred";

function read(): Set<string> {
  try { return new Set(JSON.parse(localStorage.getItem(KEY) ?? "[]") as string[]); } catch { return new Set(); }
}

export function useStarred() {
  const [starred, setStarred] = useState<Set<string>>(read);
  const toggle = (ticker: string) => {
    const next = new Set(starred);
    if (next.has(ticker)) next.delete(ticker); else next.add(ticker);
    setStarred(next);
    try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch { /* not saved: still works this visit */ }
  };
  return { starred, toggle };
}
