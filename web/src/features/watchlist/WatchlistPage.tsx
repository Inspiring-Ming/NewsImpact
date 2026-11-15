// Home: the watchlist. Two views: every company with an event, or "My companies" (starred).
// Key numbers for the view, filters, the impact map, then one compact paged table. Search
// also finds companies without an event, so any company can be found and followed.
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, type S } from "../../api/client";
import { pct, SECTORS, type Tone } from "../../shared/labels";
import { useStarred } from "../../shared/starred";
import { Term } from "../../shared/Term";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { AttentionStrip } from "./AttentionStrip";
import { ImpactMap } from "./ImpactMap";
import { KpiDetail, type Kpi } from "./KpiDetail";
import { WatchlistTable } from "./WatchlistTable";

const PAGE = 12;
const MARKETS = [["all", "All markets"], ["US", "🇺🇸 United States"], ["AU", "🇦🇺 Australia"]] as const;
type View = "events" | "mine";

// Sort orders a market user expects: newest news, largest price impact, best-supported news.
const latestAt = (c: S["CompanyCard"]) => Date.parse(c.events[0]?.updates.at(-1)?.published_at ?? c.latest_news?.published_at ?? "1970");
const SORTS: Record<string, { label: string; key: (c: S["CompanyCard"]) => number }> = {
  latest: { label: "Latest", key: latestAt },
  move: { label: "Biggest move", key: (c) => Math.max(-1, ...c.events.map((e) => (e.stock_move == null ? -1 : Math.abs(e.stock_move)))) },
  sources: { label: "Most sources", key: (c) => (c.events[0]?.sources ?? 0) + (c.events[0]?.verified ? 0.5 : 0) },
};

export function WatchlistPage({ refreshKey }: { refreshKey: number }) {
  const { data, error, loading } = useApi(api.companies, [refreshKey]);
  const overview = useApi(api.overview, [refreshKey]);
  const { starred, toggle } = useStarred();
  const [view, setView] = useState<View>("events");
  const chosen = useRef(false); // once the visitor picks a view, never switch it for them
  useEffect(() => { if (!chosen.current && starred.size) setView("mine"); }, [starred.size]);
  const [market, setMarket] = useState("all");
  const [sector, setSector] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("latest");
  const [open, setOpen] = useState<Kpi | null>(null);
  const [page, setPage] = useState(0);

  const all = data ?? [];
  const rows = useMemo(() => all
    .filter((c) => (view === "mine" ? starred.has(c.ticker) : c.events.length > 0 || query !== ""))
    .filter((c) =>
      (market === "all" || c.country === market) &&
      (sector === "all" || c.sector === sector) &&
      (!query || `${c.name} ${c.ticker}`.toLowerCase().includes(query.toLowerCase())))
    .sort((a, b) => SORTS[sort].key(b) - SORTS[sort].key(a)), [all, view, starred, market, sector, query, sort]);
  const events = rows.flatMap((c) => c.events);
  const weekAgo = Date.now() - 7 * 86_400_000;
  const thisWeek = events.filter((e) => Date.parse(e.updates[e.updates.length - 1].published_at) >= weekAgo);
  const verifiedWeek = thisWeek.filter((e) => e.verified).length;
  const unusual = events.filter((e) => e.stock_move_unusual).length;
  const biggest = rows.flatMap((c) => c.events.filter((e) => e.stock_move != null).map((e) => ({ c, e })))
    .sort((a, b) => Math.abs(b.e.stock_move!) - Math.abs(a.e.stock_move!))[0];
  // News counts follow the view: my companies, or the market and sector chosen. Unscoped,
  // the server's total is used (an article naming two companies is counted once there).
  const scoped = view === "mine" || market !== "all" || sector !== "all";
  const scope = all.filter((c) => (view !== "mine" || starred.has(c.ticker)) &&
    (market === "all" || c.country === market) && (sector === "all" || c.sector === sector));
  const inNews = scope.filter((c) => c.articles_24h > 0).length;
  const news24h = scoped ? scope.reduce((n, c) => n + c.articles_24h, 0) : overview.data?.articles_24h;
  const pages = Math.max(1, Math.ceil(rows.length / PAGE));
  const current = Math.min(page, pages - 1);
  const change = (f: () => void) => { f(); setPage(0); };
  const VIEWS: [View, string][] = [["events", "All events"], ["mine", `★ My companies${starred.size ? ` (${starred.size})` : ""}`]];

  return (
    <>
      <div className="segmented views" role="group" aria-label="View">
        {VIEWS.map(([id, name]) => (
          <button key={id} className={id === view ? "active" : ""} onClick={() => change(() => { chosen.current = true; setView(id); })}>{name}</button>
        ))}
      </div>

      {data && <AttentionStrip companies={view === "mine" ? rows : all} mine={view === "mine"} />}

      <div className="kpis">
        {([
          ["events", <Term id="eventsWeek" />, thisWeek.length, `${verifiedWeek} confirmed · ${thisWeek.length - verifiedWeek} not yet confirmed`, undefined],
          ["unusual", <Term id="unusual">Unusual stock moves</Term>, unusual, `of ${events.filter((e) => e.stock_move != null).length} events with price data`, unusual ? "warn" : undefined],
          ["biggest", <Term id="biggest" />, biggest ? pct(biggest.e.stock_move!) : "–",
            biggest ? `${biggest.c.name} vs ${biggest.c.index_name} · ${biggest.e.event_type}` : "no measured move in this view",
            biggest ? (biggest.e.stock_move! < 0 ? "bad" : "good") : undefined],
          ["news", <Term id="news24h">{view === "mine" ? "News on my companies, 24 h" : "News in 24 hours"}</Term>, news24h ?? "–",
            view === "mine" ? `${inNews} of your ${scope.length} companies in the news` : `about ${inNews} companies · from ${overview.data?.outlets_enabled ?? "–"} sources`, undefined],
        ] as [Kpi, ReactNode, ReactNode, string, Tone | undefined][]).map(([id, label, value, sub, tone]) => (
          <button key={id} className={`fact kpi-btn ${open === id ? "open" : ""}`} aria-expanded={open === id}
                  onClick={() => setOpen(open === id ? null : id)}>
            <div className="fact-label">{label}</div>
            <div className={`fact-value ${tone ?? ""}`}>{value}</div>
            <div className="fact-sub">{sub}</div>
            <div className="kpi-more">{open === id ? "Hide detail ▴" : "Show detail ▾"}</div>
          </button>
        ))}
      </div>
      {open && data && <KpiDetail kpi={open} companies={rows} newsCompanies={scope} overview={scoped ? null : overview.data} />}

      <div className="toolbar">
        <input className="search" type="search" placeholder="Search company or ticker" value={query}
               onChange={(e) => change(() => setQuery(e.target.value))} />
        <select value={market} onChange={(e) => change(() => setMarket(e.target.value))} aria-label="Market">
          {MARKETS.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
        </select>
        <select value={sector} onChange={(e) => change(() => setSector(e.target.value))} aria-label="Sector">
          <option value="all">All sectors</option>
          {SECTORS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={sort} onChange={(e) => change(() => setSort(e.target.value))} aria-label="Sort">
          {Object.entries(SORTS).map(([id, s]) => <option key={id} value={id}>Sort: {s.label}</option>)}
        </select>
      </div>
      {data && <ImpactMap companies={rows} />}

      <State error={error} loading={loading && !data}
             empty={data && rows.length === 0 && (view === "mine"
               ? <p>No companies followed yet. Click ☆ next to a company, or search for one, to follow it here.</p>
               : <p>No companies match these filters.</p>)}>
        <WatchlistTable rows={rows.slice(current * PAGE, current * PAGE + PAGE)} starred={starred} onStar={toggle} />
        <div className="pager">
          <span className="muted small">{current * PAGE + 1}–{Math.min(rows.length, current * PAGE + PAGE)} of {rows.length}</span>
          <button className="small" disabled={current === 0} onClick={() => setPage(current - 1)}>← Previous</button>
          <button className="small" disabled={current >= pages - 1} onClick={() => setPage(current + 1)}>Next →</button>
        </div>
      </State>
    </>
  );
}
