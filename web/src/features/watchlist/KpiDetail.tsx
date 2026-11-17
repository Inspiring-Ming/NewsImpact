// What opens under a key number when it is clicked: the detail behind the number, as a
// small chart. Bars are HTML (ranked lists), so labels stay readable and every row links
// to its event.
import { api, type S } from "../../api/client";
import { useApi } from "../../shared/useApi";
import { date, eventLabel, pct, vsWords } from "../../shared/labels";
import { MoveBar } from "../../shared/viz";

export type Kpi = "events" | "unusual" | "biggest" | "news";

interface Ev { c: S["CompanyCard"]; e: S["EventCard"] }

/** One row per stock move: events of a company measured over the same days share one move
 *  (it cannot be split between them), so they are one row, with both events named. */
function oneRowPerMove(rows: Ev[]): (Ev & { also: string[] })[] {
  const out: (Ev & { also: string[] })[] = [];
  for (const r of rows) {
    const twin = out.find((o) => o.c.ticker === r.c.ticker && o.e.shares_move_with.includes(r.e.event_type));
    if (twin) twin.also.push(eventLabel(r.e)); else out.push({ ...r, also: [] });
  }
  return out;
}

const INDEX_NOTE = "Each stock is compared with the index of the market it trades on: the S&P 500 for US listings, the ASX 200 for ASX listings.";

function MoveRows({ rows, limit }: { rows: Ev[]; limit?: number }) {
  const grouped = oneRowPerMove(rows).slice(0, limit);
  if (!grouped.length) return <p className="muted small">None yet.</p>;
  const span = Math.max(0.05, ...grouped.map((r) => Math.abs(r.e.stock_move!)));
  return (
    <div className="rank moves">
      {grouped.map(({ c, e, also }) => (
        <a key={e.event_id} className="rank-row" href={`#/event/${e.event_id}`}>
          <span className="rank-label"><b>{c.name}</b><span className="muted small"> · {[eventLabel(e), ...also].join(" + ")}</span>
            <span className="muted small rank-sub">{e.stock_move_period}{also.length ? " · one move on the same days: it cannot be split between the events" : ""}</span></span>
          <MoveBar value={e.stock_move!} unusual={e.stock_move_unusual} span={span} />
          <span className="rank-value"><b>{pct(e.stock_move!)}</b><span className="muted small"> {vsWords(e.stock_move!, c.index_name)}</span></span>
        </a>
      ))}
    </div>
  );
}

function CountRows({ rows }: { rows: { label: string; n: number; href?: string }[] }) {
  const max = Math.max(1, ...rows.map((r) => r.n));
  return (
    <div className="rank">
      {rows.map((r) => {
        const body = (
          <>
            <span className="rank-label">{r.label}</span>
            <span className="countbar"><span style={{ width: `${(r.n / max) * 100}%` }} /></span>
            <span className="rank-value"><b>{r.n}</b></span>
          </>
        );
        return r.href ? <a key={r.label} className="rank-row" href={r.href}>{body}</a> : <div key={r.label} className="rank-row">{body}</div>;
      })}
    </div>
  );
}

/** Articles per company, one coloured segment per source. Colours follow the source (fixed
 * order from sources.json), never its rank, so a source keeps its colour across views. */
function SourceStacks({ companies, order }: { companies: S["CompanyCard"][]; order: string[] }) {
  const max = Math.max(1, ...companies.map((c) => c.articles_24h));
  const colour = (name: string) => `var(--cat-${(Math.max(order.indexOf(name), 0) % 8) + 1})`;
  const used = order.filter((n) => companies.some((c) => (c.articles_24h_by_source[n] ?? 0) > 0));
  return (
    <>
      <div className="rank">
        {companies.map((c) => {
          const parts = Object.entries(c.articles_24h_by_source).sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]));
          const body = (
            <>
              <span className="rank-label">{c.name}</span>
              <span className="stack" style={{ width: `${(c.articles_24h / max) * 100}%` }}>
                {parts.map(([name, n]) => (
                  <span key={name} title={`${name}: ${n}`} style={{ flexGrow: n, background: colour(name) }} />
                ))}
              </span>
              <span className="rank-value"><b>{c.articles_24h}</b>
                <span className="muted small"> {parts.map(([name, n]) => `${name} ${n}`).join(" · ")}</span></span>
            </>
          );
          return c.events[0]
            ? <a key={c.ticker} className="rank-row" href={`#/event/${c.events[0].event_id}`}>{body}</a>
            : <div key={c.ticker} className="rank-row">{body}</div>;
        })}
      </div>
      <div className="legend-row small">
        {used.map((n) => <span key={n}><span className="swatch-sq" style={{ background: colour(n) }} />{n}</span>)}
      </div>
    </>
  );
}

export function KpiDetail({ kpi, companies, newsCompanies, overview }: {
  kpi: Kpi; companies: S["CompanyCard"][]; newsCompanies: S["CompanyCard"][];
  overview: S["Overview"] | null; // null = the view is narrowed, so per-source totals do not apply
}) {
  const sources = useApi(api.sources);
  const sourceOrder = (sources.data ?? []).filter((x) => x.enabled).map((x) => x.source.name.split(" - ")[0]);
  const all: Ev[] = companies.flatMap((c) => c.events.map((e) => ({ c, e })));
  const lastUpdate = (e: S["EventCard"]) => e.updates[e.updates.length - 1].published_at;
  if (kpi === "events") {
    const days = Array.from({ length: 7 }, (_, i) => new Date(Date.now() - (6 - i) * 86_400_000).toISOString().slice(0, 10));
    const week = all.filter(({ e }) => lastUpdate(e).slice(0, 10) >= days[0]).sort((a, b) => lastUpdate(b.e).localeCompare(lastUpdate(a.e)));
    const perDay = days.map((d) => week.filter(({ e }) => lastUpdate(e).slice(0, 10) === d).length);
    const max = Math.max(1, ...perDay);
    const SHOWN = 6;
    return (
      <div className="kpi-detail">
        <h3>This week, day by day <span className="muted small">· events with a new update · coloured edge = priority</span></h3>
        <div className="week-board">
          {days.map((d, i) => {
            const items = week.filter(({ e }) => lastUpdate(e).slice(0, 10) === d);
            const today = i === days.length - 1;
            return (
              <section key={d} className={`week-day${today ? " today" : ""}${items.length ? "" : " empty"}`}>
                <header>
                  <span>{today ? "Today" : new Date(d).toLocaleDateString(undefined, { weekday: "short" })}<small>{date(d)}</small></span>
                  <b>{perDay[i]}</b>
                </header>
                <span className="week-bar"><i style={{ width: `${(perDay[i] / max) * 100}%` }} /></span>
                <ul>
                  {items.slice(0, SHOWN).map(({ c, e }) => (
                    <li key={e.event_id} className={`p-${e.priority}`}>
                      <a href={`#/event/${e.event_id}`}><b>{c.name}</b><small>{eventLabel(e)}</small></a>
                    </li>
                  ))}
                </ul>
                {items.length > SHOWN && <small className="muted">+{items.length - SHOWN} more</small>}
              </section>
            );
          })}
        </div>
      </div>
    );
  }
  if (kpi === "unusual") {
    const rows = all.filter(({ e }) => e.stock_move_unusual && e.stock_move != null).sort((a, b) => a.e.stock_move! - b.e.stock_move!);
    return (
      <div className="kpi-detail">
        <h3>Unusual stock moves: larger than on 19 of 20 normal days for that stock</h3>
        <p className="small muted">{INDEX_NOTE}</p>
        <MoveRows rows={rows} />
      </div>
    );
  }
  if (kpi === "biggest") {
    const rows = all.filter(({ e }) => e.stock_move != null)
      .sort((a, b) => Math.abs(b.e.stock_move!) - Math.abs(a.e.stock_move!));
    return (
      <div className="kpi-detail">
        <h3>The 10 largest moves against the market (coloured = unusual move)</h3>
        <p className="small muted">{INDEX_NOTE} The dates under each name are the days measured: the trading day of the news and the next one.</p>
        <MoveRows rows={rows} limit={10} />
      </div>
    );
  }
  const bySource = Object.entries(overview?.articles_24h_by_source ?? {}).map(([label, n]) => ({ label, n })).sort((a, b) => b.n - a.n);
  const top = newsCompanies.filter((c) => c.articles_24h > 0).sort((a, b) => b.articles_24h - a.articles_24h).slice(0, 8);
  return (
    <div className={`kpi-detail ${overview ? "two" : ""}`}>
      {overview && <div><h3>Articles in the last 24 hours, by source</h3><CountRows rows={bySource} /></div>}
      <div>
        <h3>Most-mentioned companies, last 24 hours</h3>
        {top.length ? <SourceStacks companies={top} order={sourceOrder} /> : <p className="muted small">No news on these companies in the last 24 hours.</p>}
      </div>
    </div>
  );
}
