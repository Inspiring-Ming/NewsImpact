// The watchlist: one compact row per company, paged. Each cell pairs a number with a small
// visual; on phones every row becomes a card (see styles.css "watchlist cards").
import type { S } from "../../api/client";
import { COUNTRY, date, NO_MOVE, pct, SAID_BY, SECTOR_SHORT, tone, vsWords } from "../../shared/labels";
import { Term } from "../../shared/Term";
import { confidenceTone, Dots, Meter, MoveBar } from "../../shared/viz";

const TONE_ICON = { good: "▲", bad: "▼", neutral: "●" } as Record<string, string>;

function NewsSays({ e }: { e: S["EventCard"] }) {
  const t = tone(e.tone);
  return (
    <div className="says">
      <span className={`says-line ${t.tone}`}><span className="icon">{TONE_ICON[t.tone]}</span> {t.text} tone</span>
      <span className={`says-line ${e.is_rumour ? "warn" : ""}`}>
        <span className="icon">{e.is_rumour ? "?" : "✓"}</span> {e.is_rumour ? "Rumour" : "Stated as fact"}
      </span>
      <span className="says-line muted"><span className="icon">❝</span> {SAID_BY[e.said_by] ?? e.said_by}</span>
    </div>
  );
}

export function WatchlistTable({ rows }: { rows: S["CompanyCard"][] }) {
  return (
    <div className="table-wrap card flush">
      <table className="watchlist">
        {/* Fixed widths, so columns line up on every page whatever text a row holds. */}
        <colgroup>
          <col style={{ width: "16%" }} /><col style={{ width: "34%" }} /><col style={{ width: "16%" }} />
          <col style={{ width: "17%" }} /><col style={{ width: "17%" }} />
        </colgroup>
        <thead>
          <tr>
            <th>Company · <Term id="sector" /></th><th><Term id="event" /></th><th><Term id="says" /></th>
            <th><Term id="move" /></th><th><Term id="sources" /> · <Term id="confidence" /></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => {
            const e = c.events[0];
            const href = e ? `#/event/${e.event_id}` : undefined;
            return (
              <tr key={c.ticker} className={href ? "clickable" : ""} onClick={() => href && (window.location.hash = href)}>
                <td className="c-company">
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
                        {c.events.length > 1 && <span className="muted small">+{c.events.length - 1} more</span>}
                      </div>
                      <div className="headline-1">{e.latest_headline}</div>
                      <div className="muted small">
                        {e.latest_source} · {date(e.updates[e.updates.length - 1].published_at)}
                        {e.next_update && <> · next: <b>{e.next_update}</b></>}
                      </div>
                    </td>
                    <td className="c-says"><NewsSays e={e} /></td>
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
                      ) : <span className="muted small">{NO_MOVE[e.stock_move_status] ?? ""}</span>}
                    </td>
                    <td className="c-sources">
                      <div className="src-top"><Dots n={e.sources} /> <b>{e.sources}</b> <span className="muted small">{e.sources === 1 ? "source" : "sources"}</span></div>
                      <div className="conf"><Meter value={e.confidence} tone={confidenceTone(e.confidence)} /> <span className="small">{Math.round(e.confidence * 100)}% confidence</span></div>
                    </td>
                  </>
                ) : (
                  <td className="c-event c-news" colSpan={4}>
                    {c.latest_news ? (
                      <>
                        <span className="muted small">No event detected · latest news:</span>
                        <div className="headline-1">{c.latest_news.title}</div>
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
