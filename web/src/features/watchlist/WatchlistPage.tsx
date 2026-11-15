// Home: the watchlist. Key numbers on top, filters, then one compact paged table.
import { useMemo, useState, type ReactNode } from "react";
import { api, type S } from "../../api/client";
import { pct, SECTORS, type Tone } from "../../shared/labels";
import { Term } from "../../shared/Term";
import { State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { ImpactMap } from "./ImpactMap";
import { KpiDetail, type Kpi } from "./KpiDetail";
import { WatchlistTable } from "./WatchlistTable";

const PAGE = 12;
const MARKETS = [["all", "All markets"], ["US", "🇺🇸 US"], ["AU", "🇦🇺 Australia"]] as const;

// Sort orders a market user expects: newest news, largest price impact, best-supported news.
const latestAt = (c: S["CompanyCard"]) => Date.parse(c.events[0]?.updates.at(-1)?.published_at ?? c.latest_news?.published_at ?? "1970");
const SORTS: Record<string, { label: string; key: (c: S["CompanyCard"]) => number }> = {
  latest: { label: "Latest", key: latestAt },
  move: { label: "Biggest move", key: (c) => Math.max(-1, ...c.events.map((e) => (e.stock_move == null ? -1 : Math.abs(e.stock_move)))) },
  sources: { label: "Most sources", key: (c) => (c.events[0]?.sources ?? 0) + (c.events[0]?.confidence ?? 0) },
};

export function WatchlistPage({ refreshKey }: { refreshKey: number }) {
  const { data, error, loading } = useApi(api.companies, [refreshKey]);
  const overview = useApi(api.overview, [refreshKey]);
  const [market, setMarket] = useState("all");
  const [sector, setSector] = useState("all");
  const [eventsOnly, setEventsOnly] = useState(true);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("latest");
  const [open, setOpen] = useState<Kpi | null>(null);
  const [page, setPage] = useState(0);

  const all = data ?? [];
  const events = all.flatMap((c) => c.events);
  const weekAgo = Date.now() - 7 * 86_400_000, dayAgo = Date.now() - 86_400_000;
  const thisWeek = events.filter((e) => Date.parse(e.updates[e.updates.length - 1].published_at) >= weekAgo);
  const unusual = events.filter((e) => e.stock_move_unusual).length;
  const biggest = all.flatMap((c) => c.events.filter((e) => e.stock_move != null).map((e) => ({ c, e })))
    .sort((a, b) => Math.abs(b.e.stock_move!) - Math.abs(a.e.stock_move!))[0];
  const inNews = all.filter((c) => c.latest_news && Date.parse(c.latest_news.published_at) >= dayAgo).length;
  const rows = useMemo(() => all.filter((c) =>
    (market === "all" || c.country === market) &&
    (sector === "all" || c.sector === sector) &&
    (!eventsOnly || c.events.length > 0) &&
    (!query || `${c.name} ${c.ticker}`.toLowerCase().includes(query.toLowerCase())),
  ).sort((a, b) => SORTS[sort].key(b) - SORTS[sort].key(a)), [all, market, sector, eventsOnly, query, sort]);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE));
  const current = Math.min(page, pages - 1);
  const change = (f: () => void) => { f(); setPage(0); };

  return (
    <>
      <div className="kpis">
        {([
          ["events", <Term id="eventsWeek" />, thisWeek.length, `${thisWeek.filter((e) => e.ongoing).length} still developing · ${events.length} in total`, undefined],
          ["unusual", <Term id="unusual">Unusual stock moves</Term>, unusual, `of ${events.filter((e) => e.stock_move != null).length} events with price data`, unusual ? "warn" : undefined],
          ["biggest", <Term id="biggest" />, biggest ? pct(biggest.e.stock_move!) : "–",
            biggest ? `${biggest.c.name} vs ${biggest.c.index_name} · ${biggest.e.event_type}` : "no price data yet",
            biggest ? (biggest.e.stock_move! < 0 ? "bad" : "good") : undefined],
          ["news", <Term id="news24h" />, overview.data?.articles_24h ?? "–", `about ${inNews} companies · from ${overview.data?.outlets_enabled ?? "–"} sources`, undefined],
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
      {open && data && <KpiDetail kpi={open} companies={all} overview={overview.data} />}

      <div className="toolbar">
        <input className="search" type="search" placeholder="Search company or ticker" value={query}
               onChange={(e) => change(() => setQuery(e.target.value))} />
        <div className="segmented" role="group" aria-label="Market">
          {MARKETS.map(([id, name]) => (
            <button key={id} className={id === market ? "active" : ""} onClick={() => change(() => setMarket(id))}>{name}</button>
          ))}
        </div>
        <select value={sector} onChange={(e) => change(() => setSector(e.target.value))} aria-label="Sector">
          <option value="all">All sectors</option>
          {SECTORS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={sort} onChange={(e) => change(() => setSort(e.target.value))} aria-label="Sort">
          {Object.entries(SORTS).map(([id, s]) => <option key={id} value={id}>Sort: {s.label}</option>)}
        </select>
        <div className="segmented" role="group" aria-label="Show">
          <button className={eventsOnly ? "active" : ""} onClick={() => change(() => setEventsOnly(true))}>With events</button>
          <button className={!eventsOnly ? "active" : ""} onClick={() => change(() => setEventsOnly(false))}>All companies</button>
        </div>
      </div>

      {data && <ImpactMap companies={rows} />}

      <State error={error} loading={loading && !data}
             empty={data && rows.length === 0 && (
               <p>No companies match. {eventsOnly && <button className="small" onClick={() => setEventsOnly(false)}>Show all companies</button>}</p>
             )}>
        <WatchlistTable rows={rows.slice(current * PAGE, current * PAGE + PAGE)} />
        <div className="pager">
          <span className="muted small">{current * PAGE + 1}–{Math.min(rows.length, current * PAGE + PAGE)} of {rows.length}</span>
          <button className="small" disabled={current === 0} onClick={() => setPage(current - 1)}>← Previous</button>
          <button className="small" disabled={current >= pages - 1} onClick={() => setPage(current + 1)}>Next →</button>
        </div>
      </State>
    </>
  );
}
