// The watchlist: one compact row per company, paged. Four columns, each answering one
// question: who, what happened, how did the stock react, how well is it sourced.
// On phones every row becomes a card (see styles.css "watchlist cards").
import type { S } from "../../api/client";
import { COUNTRY, date, NO_MOVE, pct, SECTOR_SHORT, vsWords } from "../../shared/labels";
import { Signals } from "../../shared/Signals";
import { SourceBadge } from "../../shared/SourceBadge";
import { Term } from "../../shared/Term";
import { Dots, MoveBar } from "../../shared/viz";

export function WatchlistTable({ rows, starred, onStar }: {
  rows: S["CompanyCard"][]; starred: Set<string>; onStar: (ticker: string) => void;
}) {
  return (
    <div className="table-wrap card flush">
      <table className="watchlist">
        {/* Fixed widths, so columns line up on every page whatever text a row holds. */}
        <colgroup>
          <col style={{ width: "19%" }} /><col style={{ width: "45%" }} /><col style={{ width: "19%" }} /><col style={{ width: "17%" }} />
        </colgroup>
        <thead>
          <tr>
            <th>Company · <Term id="sector" /></th><th><Term id="event" /></th>
            <th><Term id="move" /></th><th><Term id="sources" /></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => {
            const e = c.events[0];
            const href = e ? `#/event/${e.event_id}` : undefined;
            return (
              <tr key={c.ticker} className={href ? "clickable" : ""} onClick={() => href && (window.location.hash = href)}>
                <td className="c-company">
                  <button className={`star ${starred.has(c.ticker) ? "on" : ""}`} aria-pressed={starred.has(c.ticker)}
                          title={starred.has(c.ticker) ? "Stop following" : "Follow this company"}
                          onClick={(ev) => { ev.stopPropagation(); onStar(c.ticker); }}>{starred.has(c.ticker) ? "★" : "☆"}</button>
                  <b>{c.name}</b>
                  <div className="muted small">
                    {COUNTRY[c.country]?.flag} {c.ticker} · <Term tip={`${c.sector} (GICS sector)`}>{SECTOR_SHORT[c.sector] ?? c.sector}</Term>
                  </div>
                </td>
                {e ? (
                  <>
                    <td className="c-event">
                      <div className="event-top">
                        <span className="tag">{e.event_type}</span>
                        <span className="progress" title={`${e.updates.length} of ${e.stages_total} usual updates`}>
                          <Dots n={e.updates.length} of={Math.max(e.stages_total, e.updates.length)} />
                        </span>
                        <Signals e={e} />
                        {c.events.length > 1 && <span className="muted small">+{c.events.length - 1} more</span>}
                      </div>
                      <a className="headline-1" href={e.latest_url} target="_blank" rel="noreferrer"
                         onClick={(ev) => ev.stopPropagation()}>{e.latest_headline} ↗</a>
                      <div className="muted small">
                        {e.latest_source} · {date(e.updates[e.updates.length - 1].published_at)}
                        {e.next_update && <> · next: <b>{e.next_update}</b></>}
                      </div>
                    </td>
                    <td className="c-move">
                      {e.stock_move != null ? (
                        <>
                          <div className="move-top">
                            <b className={e.stock_move_unusual ? (e.stock_move < 0 ? "bad" : "good") : ""}>{pct(e.stock_move)}</b>
                            <MoveBar value={e.stock_move} unusual={e.stock_move_unusual} />
                          </div>
                          <div className="muted small">{vsWords(e.stock_move, c.index_name)} · {e.stock_move_period}</div>
                          <div className={`small ${e.stock_move_unusual ? "warn" : "muted"}`}>{e.stock_move_unusual ? "⚠ Unusual move" : "Normal range"}</div>
                        </>
                      ) : e.move_so_far != null ? (
                        <>
                          <div className="move-top"><b className="muted">{pct(e.move_so_far)}</b><MoveBar value={e.move_so_far} unusual={false} /></div>
                          <div className="muted small">so far, to {date(e.so_far_through!)} close</div>
                          <div className="small muted"><Term id="provisional">Provisional</Term></div>
                        </>
                      ) : <span className="muted small">{NO_MOVE[e.stock_move_status] ?? ""}</span>}
                    </td>
                    <td className="c-sources"><SourceBadge confirmed={e.verified} names={e.source_names} /></td>
                  </>
                ) : (
                  <td className="c-event c-news" colSpan={3}>
                    {c.latest_news ? (
                      <>
                        <span className="muted small">No event detected · latest news:</span>
                        <a className="headline-1" href={c.latest_news.url} target="_blank" rel="noreferrer"
                           onClick={(ev) => ev.stopPropagation()}>{c.latest_news.title} ↗</a>
                        <div className="muted small">{c.latest_news.source} · {date(c.latest_news.published_at)}</div>
                      </>
                    ) : <span className="muted small">No recent news</span>}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
