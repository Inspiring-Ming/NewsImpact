// "My companies": the tickers being followed. Kept on the server, because alerts (e.g.
// Discord) are sent for them after each monitor round. One list for now: a single user.
import { useEffect, useState } from "react";
import { api } from "../api/client";

export function useStarred() {
  const [starred, setStarred] = useState<Set<string>>(new Set());
  useEffect(() => { api.watchlist().then((t) => setStarred(new Set(t))).catch(() => undefined); }, []);
  const toggle = (ticker: string) => {
    const follow = !starred.has(ticker);
    const next = new Set(starred);
    if (follow) next.add(ticker); else next.delete(ticker);
    setStarred(next); // show it at once; the server's answer then confirms the list
    (follow ? api.follow(ticker) : api.unfollow(ticker)).then((t) => setStarred(new Set(t))).catch(() => setStarred(starred));
  };
  return { starred, toggle };
}
