// "Needs attention": every event in the current view that is Act now or Check, most
// urgent first, each with its brief and the single most useful next step.
import type { S } from "../../api/client";
import { PriorityBadge } from "../../shared/badges";

const RANK: Record<string, number> = { act: 0, check: 1, background: 2 };

export function attentionItems(companies: S["CompanyCard"][]) {
  return companies.flatMap((c) => c.events.map((e) => ({ c, e })))
    .filter(({ e }) => e.priority !== "background")
    .sort((a, b) => RANK[a.e.priority] - RANK[b.e.priority]
      || b.e.updates[b.e.updates.length - 1].published_at.localeCompare(a.e.updates[a.e.updates.length - 1].published_at));
}

export function NeedsAttention({ companies }: { companies: S["CompanyCard"][] }) {
  const items = attentionItems(companies);
  if (items.length === 0) {
    return <div className="state empty">Nothing urgent here right now: no confirmed news with a new update, and no unusual stock move.</div>;
  }
  return (
    <div className="attention-cards">
      {items.map(({ c, e }) => (
        <a key={e.event_id} className="card attention-card" href={`#/event/${e.event_id}`}>
          <div className="event-top"><PriorityBadge e={e} /><span className="tag">{e.event_type}</span></div>
          <b>{c.name}</b>
          <p className="small">{e.brief[0]}</p>
          {e.checks[1] && <p className="small next-step">→ {e.checks[1].text}</p>}
        </a>
      ))}
    </div>
  );
}
