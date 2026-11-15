// The watchlist: one compact row per company, paged, so the page never gets long.
import type { S } from "../../api/client";
import { COUNTRY, date, pct } from "../../shared/labels";

export function WatchlistTable({ rows }: { rows: S["CompanyCard"][] }) {
  return (
    <div className="table-wrap card flush">
      <table className="watchlist">
        <thead>
          <tr>
            <th>Company</th><th>Sector</th><th>Latest event</th>
            <th className="num">Stock vs index</th><th className="num">Sources</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => {
            const e = c.events[0];
            const href = e ? `#/event/${e.event_id}` : undefined;
            const country = COUNTRY[c.country];
            return (
              <tr key={c.ticker} className={href ? "clickable" : ""} onClick={() => href && (window.location.hash = href)}>
                <td>
                  <b>{c.name}</b>
                  <div className="muted small">{country?.flag} {c.ticker}</div>
                </td>
                <td className="small muted">{c.sector}</td>
                <td className="event-cell">
                  {e ? (
                    <>
                      <span className="tag">{e.event_type}</span>
                      {c.events.length > 1 && <span className="muted small"> +{c.events.length - 1} more</span>}
                      <div className="headline-1">{e.latest_headline}</div>
                      <div className="muted small">{e.latest_source} · {date(e.updates[e.updates.length - 1].published_at)}</div>
                    </>
                  ) : c.latest_news ? (
                    <>
                      <div className="headline-1 muted">{c.latest_news.title}</div>
                      <div className="muted small">{c.latest_news.source} · {date(c.latest_news.published_at)} · no event</div>
                    </>
                  ) : <span className="muted small">No recent news</span>}
                </td>
                <td className="num">
                  {e && e.stock_move != null ? (
                    <>
                      <b className={e.stock_move_unusual ? (e.stock_move < 0 ? "bad" : "good") : ""}>{pct(e.stock_move)}</b>
                      <div className="muted small">vs {c.index_name} · {e.stock_move_period}</div>
                      <div className={`small ${e.stock_move_unusual ? "warn" : "muted"}`}>{e.stock_move_unusual ? "Unusual move" : "Normal range"}</div>
                    </>
                  ) : <span className="muted">—</span>}
                </td>
                <td className="num">
                  {e ? (
                    <>
                      <b>{e.sources}</b>
                      <div className="muted small">{Math.round(e.source_reliability * 100)}% reliable</div>
                    </>
                  ) : <span className="muted">—</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
