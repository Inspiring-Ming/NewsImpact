// The watchlist: one compact row per company, paged, so the page never gets long.
// Every column header explains itself on hover (see TERMS in labels.ts).
import type { S } from "../../api/client";
import { COUNTRY, date, NO_MOVE, pct, SAID_BY, SECTOR_SHORT, tone, vsWords } from "../../shared/labels";
import { Pill } from "../../shared/ui";
import { Term } from "../../shared/Term";

function NewsSays({ e }: { e: S["EventCard"] }) {
  const t = tone(e.tone);
  return (
    <div className="says">
      <div className="says-chips">
        <Pill tone={t.tone}>{t.text}</Pill>
        <Pill tone={e.is_rumour ? "warn" : "neutral"}>{e.is_rumour ? "Rumour" : "Stated as fact"}</Pill>
      </div>
      <div className="muted small">From: {SAID_BY[e.said_by] ?? e.said_by}</div>
      {e.next_update && <div className="small">Next: <b>{e.next_update}</b></div>}
    </div>
  );
}

export function WatchlistTable({ rows }: { rows: S["CompanyCard"][] }) {
  return (
    <div className="table-wrap card flush">
      <table className="watchlist">
        <thead>
          <tr>
            <th>Company · <Term id="sector" /></th><th><Term id="event" /></th><th><Term id="says" /></th>
            <th className="num"><Term id="move" /></th>
            <th className="num"><Term id="sources" /> · <Term id="confidence" /></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => {
            const e = c.events[0];
            const href = e ? `#/event/${e.event_id}` : undefined;
            return (
              <tr key={c.ticker} className={href ? "clickable" : ""} onClick={() => href && (window.location.hash = href)}>
                <td className="company-cell">
                  <b>{c.name}</b>
                  <div className="muted small">
                    {COUNTRY[c.country]?.flag} {c.ticker} · <Term tip={`${c.sector} (GICS sector)`}>{SECTOR_SHORT[c.sector] ?? c.sector}</Term>
                  </div>
                </td>
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
                <td>{e ? <NewsSays e={e} /> : <span className="muted">—</span>}</td>
                <td className="num">
                  {e && e.stock_move != null ? (
                    <>
                      <b className={e.stock_move_unusual ? (e.stock_move < 0 ? "bad" : "good") : ""}>{pct(e.stock_move)}</b>
                      <div className="muted small">{vsWords(e.stock_move, c.index_name)}</div>
                      <div className={`small ${e.stock_move_unusual ? "warn" : "muted"}`}>
                        {e.stock_move_period} · {e.stock_move_unusual ? "Unusual move" : "Normal range"}
                      </div>
                    </>
                  ) : e ? <span className="muted small">{NO_MOVE[e.stock_move_status] ?? "—"}</span> : <span className="muted">—</span>}
                </td>
                <td className="num">
                  {e ? (
                    <>
                      <b>{e.sources} {e.sources === 1 ? "source" : "sources"}</b>
                      <div className={`small ${e.confidence >= 0.9 ? "good" : "warn"}`}>{Math.round(e.confidence * 100)}% confidence</div>
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
