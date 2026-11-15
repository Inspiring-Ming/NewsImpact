// Home: the watchlist. Key numbers on top, filters, then one compact paged table.
import { useMemo, useState } from "react";
import { api } from "../../api/client";
import { SECTORS } from "../../shared/labels";
import { Fact, State } from "../../shared/ui";
import { useApi } from "../../shared/useApi";
import { WatchlistTable } from "./WatchlistTable";

const PAGE = 12;
const MARKETS = [["all", "All markets"], ["US", "🇺🇸 US"], ["AU", "🇦🇺 Australia"]] as const;

export function WatchlistPage({ refreshKey }: { refreshKey: number }) {
  const { data, error, loading } = useApi(api.companies, [refreshKey]);
  const overview = useApi(api.overview, [refreshKey]);
  const [market, setMarket] = useState("all");
  const [sector, setSector] = useState("all");
  const [eventsOnly, setEventsOnly] = useState(true);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);

  const all = data ?? [];
  const events = all.flatMap((c) => c.events);
  const rows = useMemo(() => all.filter((c) =>
    (market === "all" || c.country === market) &&
    (sector === "all" || c.sector === sector) &&
    (!eventsOnly || c.events.length > 0) &&
    (!query || `${c.name} ${c.ticker}`.toLowerCase().includes(query.toLowerCase())),
  ), [all, market, sector, eventsOnly, query]);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE));
  const current = Math.min(page, pages - 1);
  const change = (f: () => void) => { f(); setPage(0); };

  return (
    <>
      <div className="kpis">
        <Fact label="Companies tracked" value={all.length || "–"} sub="large caps, US and Australia" />
        <Fact label="Events" value={events.length} sub={`${events.filter((e) => e.ongoing).length} still developing`} />
        <Fact label="Unusual stock moves" value={events.filter((e) => e.stock_move_unusual).length} sub="beyond normal daily swings" tone="warn" />
        <Fact label="News sources" value={overview.data?.outlets_enabled ?? "–"} sub="read automatically" />
      </div>

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
        <div className="segmented" role="group" aria-label="Show">
          <button className={eventsOnly ? "active" : ""} onClick={() => change(() => setEventsOnly(true))}>With events</button>
          <button className={!eventsOnly ? "active" : ""} onClick={() => change(() => setEventsOnly(false))}>All companies</button>
        </div>
      </div>

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
