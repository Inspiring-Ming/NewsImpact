// What opens under a key number when it is clicked: the detail behind the number, as a
// small chart. Bars are HTML (ranked lists), so labels stay readable and every row links
// to its event.
import type { S } from "../../api/client";
import { date, pct, vsWords } from "../../shared/labels";
import { MoveBar } from "../../shared/viz";

export type Kpi = "events" | "unusual" | "biggest" | "news";

interface Ev { c: S["CompanyCard"]; e: S["EventCard"] }

function MoveRows({ rows }: { rows: Ev[] }) {
  if (!rows.length) return <p className="muted small">None yet.</p>;
  const span = Math.max(0.05, ...rows.map((r) => Math.abs(r.e.stock_move!)));
  return (
    <div className="rank moves">
      {rows.map(({ c, e }) => (
        <a key={e.event_id} className="rank-row" href={`#/event/${e.event_id}`}>
          <span className="rank-label"><b>{c.name}</b><span className="muted small"> · {e.event_type}</span></span>
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

export function KpiDetail({ kpi, companies, newsCompanies, overview }: {
  kpi: Kpi; companies: S["CompanyCard"][]; newsCompanies: S["CompanyCard"][];
  overview: S["Overview"] | null; // null = the view is narrowed, so per-source totals do not apply
}) {
  const all: Ev[] = companies.flatMap((c) => c.events.map((e) => ({ c, e })));
  const lastUpdate = (e: S["EventCard"]) => e.updates[e.updates.length - 1].published_at;
  if (kpi === "events") {
    const days = Array.from({ length: 7 }, (_, i) => new Date(Date.now() - (6 - i) * 86_400_000).toISOString().slice(0, 10));
    const week = all.filter(({ e }) => lastUpdate(e).slice(0, 10) >= days[0]).sort((a, b) => lastUpdate(b.e).localeCompare(lastUpdate(a.e)));
    const perDay = days.map((d) => week.filter(({ e }) => lastUpdate(e).slice(0, 10) === d).length);
    const max = Math.max(1, ...perDay);
    return (
      <div className="kpi-detail">
        <h3>Events with a new update, by day</h3>
        <div className="day-cols">
          {days.map((d, i) => (
            <div key={d} className="day-col">
              <span className="day-n">{perDay[i] || ""}</span>
              <span className="day-bar" style={{ height: `${(perDay[i] / max) * 100}%` }} />
              <span className="day-label">{date(d)}</span>
            </div>
          ))}
        </div>
        <h3>This week's events</h3>
        <div className="chips-list">
          {week.map(({ c, e }) => (
            <a key={e.event_id} href={`#/event/${e.event_id}`} className="event-chip">
              <b>{c.name}</b> <span className="tag">{e.event_type}</span> <span className="muted small">{date(lastUpdate(e))}</span>
            </a>
          ))}
        </div>
      </div>
    );
  }
  if (kpi === "unusual") {
    const rows = all.filter(({ e }) => e.stock_move_unusual && e.stock_move != null).sort((a, b) => a.e.stock_move! - b.e.stock_move!);
    return (
      <div className="kpi-detail">
        <h3>Unusual stock moves: larger than on 19 of 20 normal days for that stock</h3>
        <MoveRows rows={rows} />
      </div>
    );
  }
  if (kpi === "biggest") {
    const rows = all.filter(({ e }) => e.stock_move != null)
      .sort((a, b) => Math.abs(b.e.stock_move!) - Math.abs(a.e.stock_move!)).slice(0, 10);
    return (
      <div className="kpi-detail">
        <h3>The 10 largest moves against the market (bar colour = unusual move)</h3>
        <MoveRows rows={rows} />
      </div>
    );
  }
  const bySource = Object.entries(overview?.articles_24h_by_source ?? {}).map(([label, n]) => ({ label, n })).sort((a, b) => b.n - a.n);
  const byCompany = newsCompanies.filter((c) => c.articles_24h > 0).sort((a, b) => b.articles_24h - a.articles_24h).slice(0, 8)
    .map((c) => ({ label: c.name, n: c.articles_24h, href: c.events[0] ? `#/event/${c.events[0].event_id}` : undefined }));
  return (
    <div className={`kpi-detail ${overview ? "two" : ""}`}>
      {overview && <div><h3>Articles in the last 24 hours, by source</h3><CountRows rows={bySource} /></div>}
      <div>
        <h3>Most-mentioned companies, last 24 hours</h3>
        {byCompany.length ? <CountRows rows={byCompany} /> : <p className="muted small">No news on these companies in the last 24 hours.</p>}
      </div>
    </div>
  );
}
