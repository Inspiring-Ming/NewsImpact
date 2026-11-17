// The watchlist as a feed: one row per company, newest first, under day headings when sorted
// by latest. A coloured edge = priority; then who, what happened, how the stock did against its
// market (number + line), and how well it is sourced. On phones each row becomes a card.
import type { S } from "../../api/client";
import { COUNTRY, date, eventLabel, NO_MOVE, pct, SECTOR_SHORT, SECTORS, tone, vsWords } from "../../shared/labels";
import { level } from "../../shared/priority";
import { Term } from "../../shared/Term";
import { Dots, Sparkline } from "../../shared/viz";
import { Confirmation, PriorityBadge } from "../../shared/badges";

const latestAt = (c: S["CompanyCard"]) =>
  c.events[0] ? c.events[0].updates[c.events[0].updates.length - 1].published_at : c.latest_news?.published_at;

function dayHeading(iso: string): string {
  const d = new Date(iso), today = new Date();
  const days = Math.round((new Date(today.toDateString()).getTime() - new Date(d.toDateString()).getTime()) / 86_400_000);
  return days === 0 ? "Today" : days === 1 ? "Yesterday" : d.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "short" });
}

export function WatchlistTable({ rows, starred, onStar, byDay }: {
  rows: S["CompanyCard"][]; starred: Set<string>; onStar: (ticker: string) => void; byDay: boolean;
}) {
  let last = "";
  return (
    <div className="feed" role="list">
      <div className="feed-head" aria-hidden="true">
        <span>Company</span><span><Term id="event" /></span><span><Term id="move" /></span><span><Term id="sources" /></span>
      </div>
      {rows.map((c) => {
        const at = latestAt(c), heading = byDay && at ? dayHeading(at) : "";
        const showHeading = heading && heading !== last;
        last = heading || last;
        return (
          <div key={c.ticker} role="listitem">
            {showHeading && <h3 className="feed-day">{heading}</h3>}
            <Row c={c} starred={starred.has(c.ticker)} onStar={onStar} />
          </div>
        );
      })}
    </div>
  );
}

function Row({ c, starred, onStar }: { c: S["CompanyCard"]; starred: boolean; onStar: (ticker: string) => void }) {
  const e = c.events[0];
  const href = e ? `#/event/${e.event_id}` : undefined;
  const p = e ? level(e.priority) : null;
  const go = () => href && (window.location.hash = href);
  return (
    <div className={`feed-row ${p ? `p-${p.id}` : "quiet"}${href ? " clickable" : ""}`} onClick={go} tabIndex={href ? 0 : undefined}
         onKeyDown={(ev) => { if (href && ev.key === "Enter" && ev.target === ev.currentTarget) go(); }}>
      <div className="f-company">
        <button className={`star ${starred ? "on" : ""}`} aria-pressed={starred} title={starred ? "Stop following" : "Follow this company"}
                onClick={(ev) => { ev.stopPropagation(); onStar(c.ticker); }}>{starred ? "★" : "☆"}</button>
        <div>
          <b>{c.name}</b>
          <div className="small muted">
            {COUNTRY[c.country]?.flag} {c.ticker}{" "}
            <span className={`sector-chip sec-${SECTORS.indexOf(c.sector) + 1}`}>
              <Term tip={`${c.sector} (GICS sector)`}>{SECTOR_SHORT[c.sector] ?? c.sector}</Term>
            </span>
          </div>
        </div>
      </div>
      {e ? <EventCells c={c} e={e} /> : (
        <div className="f-news">
          {c.latest_news ? <>
            <span className="small muted">No event · latest news </span>
            <a href={c.latest_news.url} target="_blank" rel="noreferrer" onClick={(ev) => ev.stopPropagation()}>{c.latest_news.title} ↗</a>
            <span className="small muted"> · {c.latest_news.source}, {date(c.latest_news.published_at)}</span>
          </> : <span className="small muted">No recent news</span>}
        </div>
      )}
    </div>
  );
}

function EventCells({ c, e }: { c: S["CompanyCard"]; e: S["EventCard"] }) {
  const t = tone(e.tone);
  const move = e.stock_move ?? e.move_so_far;
  const updated = e.updates[e.updates.length - 1].published_at;
  return (
    <>
      <div className="f-event">
        <div className="f-tags">
          {e.priority !== "background" && <PriorityBadge e={e} />}
          <span className="tag">{eventLabel(e)}</span>
          <Term id="tone"><span className={`f-tone ${t.tone}`} aria-label={t.text}>{t.icon}</span></Term>
          {e.is_rumour && <Term id="rumour"><span className="f-rumour">rumour</span></Term>}
          {e.updates.length > 1 && <span className="small muted">{e.updates.length} updates</span>}
        </div>
        <a className="f-headline" href={e.latest_url} target="_blank" rel="noreferrer" onClick={(ev) => ev.stopPropagation()}>{e.latest_headline}</a>
        <div className="small muted">
          {e.latest_source} · {date(updated)}{e.next_update && <> · possible next: <b>{e.next_update}</b></>}
        </div>
      </div>
      <div className="f-move">
        {move != null ? <>
          <div className="f-move-top">
            <b className={`f-move-n ${e.stock_move_unusual ? (move < 0 ? "bad" : "good") : ""}`}>{pct(move)}</b>
            {e.spark.length > 1 && <Sparkline values={e.spark} eventAt={e.spark_event_at} label={`${c.name} vs ${c.index_name}, each close from just before the event (dashed line = no difference)`} />}
          </div>
          <div className="small muted">
            {e.stock_move != null
              ? <>{vsWords(move, c.index_name)} · {e.stock_move_unusual ? <span className="warn">⚠ unusual</span> : "normal range"}</>
              : <>so far, to {date(e.so_far_through!)} · <Term id="provisional">provisional</Term></>}
          </div>
        </> : <span className="small muted">{NO_MOVE[e.stock_move_status] ?? ""}</span>}
      </div>
      <div className="f-sources">
        <Term tip={e.source_names.length ? `Reported by: ${e.source_names.join(", ")}` : "No source listed"}>
          <span className="f-src"><Dots n={e.sources} /> <b>{e.sources}</b> {e.sources === 1 ? "source" : "sources"}</span>
        </Term>
        <Confirmation confirmed={e.verified} />
      </div>
    </>
  );
}
