// Priorities: a board with one column per priority level (shared/priority.ts), most urgent
// on the left. Each card shows, at a glance, why it is there: the stock move as a bar,
// how many sources and whether it is confirmed, and the single most useful next step.
import type { S } from "../../api/client";
import { Signals } from "../../shared/badges";
import { pct } from "../../shared/labels";
import { byPriority, LEVELS } from "../../shared/priority";
import { Dots, MoveBar } from "../../shared/viz";

function PriorityCard({ c, e }: { c: S["CompanyCard"]; e: S["EventCard"] }) {
  const move = e.stock_move ?? e.move_so_far;
  return (
    <a className="pcard" href={`#/event/${e.event_id}`}>
      <div className="pcard-head">
        <b>{c.name}</b>
        <span className="tag">{e.event_type}</span>
      </div>
      <p className="pcard-reason small">{e.priority_reason}</p>
      <div className="pcard-facts">
        <span className="pcard-fact">
          {move == null ? <span className="muted">move not measured yet</span> : (
            <><MoveBar value={move} unusual={e.stock_move_unusual} />
              <b className={e.stock_move_unusual ? (move < 0 ? "bad" : "good") : ""}>{pct(move)}</b>
              {e.stock_move == null && <span className="muted"> so far</span>}</>
          )}
        </span>
        <span className="pcard-fact">
          <Dots n={e.sources} /> {e.sources} {e.sources === 1 ? "source" : "sources"}
          <span className={e.verified ? "good" : "warn"}> · {e.verified ? "✓ confirmed" : "○ not yet confirmed"}</span>
        </span>
      </div>
      <Signals e={e} />
      {e.checks[1] && <p className="pcard-next small">→ {e.checks[1].text}</p>}
    </a>
  );
}

export function priorityCount(companies: S["CompanyCard"][]) {
  const shown = new Set(LEVELS.filter((l) => l.onBoard).map((l) => l.id));
  return byPriority(companies).filter(({ e }) => shown.has(e.priority)).length;
}

export function PriorityBoard({ companies }: { companies: S["CompanyCard"][] }) {
  const items = byPriority(companies);
  const lanes = LEVELS.filter((l) => l.onBoard);
  return (
    <div className="board" style={{ gridTemplateColumns: `repeat(${lanes.length}, minmax(0, 1fr))` }}>
      {lanes.map((l) => {
        const cards = items.filter(({ e }) => e.priority === l.id);
        return (
          <section key={l.id} className={`lane ${l.id}`}>
            <header className="lane-head">
              <span className={`priority ${l.id}`}><span className="pdot" />{l.text}</span>
              <span className="lane-count">{cards.length}</span>
            </header>
            <p className="small muted lane-meaning">{l.meaning}</p>
            {cards.length
              ? cards.map(({ c, e }) => <PriorityCard key={e.event_id} c={c} e={e} />)
              : <p className="small muted lane-empty">Nothing here right now.</p>}
          </section>
        );
      })}
    </div>
  );
}
