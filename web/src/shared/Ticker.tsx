// Live ticker under the header: the latest events, newest first, each linking to its event
// page. Company, event, and the stock's move against its index (provisional while the
// measurement window is still open). It scrolls like a market tape and stops on hover or
// keyboard focus; with motion turned off it stays still and scrolls sideways by hand.
import { api } from "../api/client";
import { date, eventLabel, pct } from "./labels";
import { useApi } from "./useApi";

const MAX = 24;

export function Ticker({ refreshKey }: { refreshKey: number }) {
  const { data } = useApi(api.companies, [refreshKey]);
  const items = (data ?? [])
    .flatMap((c) => c.events.map((e) => {
      const at = Math.max(...e.updates.map((u) => Date.parse(u.published_at)));
      const move = e.stock_move ?? (e.stock_move_status === "pending" ? e.move_so_far : null);
      return { c, e, at, move, provisional: e.stock_move == null && move != null };
    }))
    .sort((a, b) => b.at - a.at)
    .slice(0, MAX);
  if (!items.length) return null;

  const list = (copy: boolean) => (
    <ul className="ticker-list" aria-hidden={copy || undefined}>
      {items.map(({ c, e, at, move, provisional }) => (
        <li key={e.event_id}>
          <a href={`#/event/${e.event_id}`} tabIndex={copy ? -1 : undefined}
             aria-label={copy ? undefined : `${c.name}, ${eventLabel(e)}${move != null ? `, ${pct(move)} vs ${c.index_name}${provisional ? " so far" : ""}` : ""}, ${date(new Date(at).toISOString())}`}>
            <b>{c.name}</b>
            <span className="ticker-event">{eventLabel(e)}</span>
            {move != null && (
              <span className={`ticker-move ${move < 0 ? "bad" : "good"}`}>
                {move < 0 ? "▼" : "▲"} {pct(move)}{provisional && <span className="ticker-so-far"> so far</span>}
              </span>
            )}
            <span className="ticker-date">{date(new Date(at).toISOString())}</span>
          </a>
        </li>
      ))}
    </ul>
  );

  return (
    <section className="ticker" aria-label="Latest events">
      <span className="ticker-live"><span className="dot live" />Latest</span>
      <div className="ticker-viewport">
        <div className="ticker-track" style={{ animationDuration: `${items.length * 6}s` }}>
          {list(false)}
          {list(true)}
        </div>
      </div>
    </section>
  );
}
