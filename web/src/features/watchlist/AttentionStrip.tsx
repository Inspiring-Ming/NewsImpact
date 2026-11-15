// "Needs your attention": up to three events that matter most right now, each with the
// single most useful next step. Followed companies when there are any, else everything.
import type { S } from "../../api/client";
import { PriorityBadge } from "../../shared/badges";

const RANK: Record<string, number> = { act: 0, check: 1, background: 2 };

export function AttentionStrip({ companies, mine }: { companies: S["CompanyCard"][]; mine: boolean }) {
  const items = companies.flatMap((c) => c.events.map((e) => ({ c, e })))
    .filter(({ e }) => e.priority !== "background")
    .sort((a, b) => RANK[a.e.priority] - RANK[b.e.priority]
      || b.e.updates[b.e.updates.length - 1].published_at.localeCompare(a.e.updates[a.e.updates.length - 1].published_at))
    .slice(0, 3);
  return (
    <section className="attention">
      <h2>{mine ? "Needs your attention" : "Needs attention"}</h2>
      {items.length === 0 ? (
        <p className="muted small">Nothing urgent {mine ? "for your companies" : ""} right now: no confirmed news with a new update or an unusual move.</p>
      ) : (
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
      )}
    </section>
  );
}
