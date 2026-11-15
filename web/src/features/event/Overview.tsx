// Overview: the share price against its market with each update marked, then two short
// cards: what to watch next, and what published research says usually happens.
import { useNames } from "../../shared/names";
import { PriceChart } from "../../shared/PriceChart";
import type { EventData } from "./context";

export function Overview({ company, card, assessment, prices }: EventData) {
  const { title } = useNames();
  const [lead, ...more] = card.research;
  return (
    <>
      <div className="card">
        <h2>Share price vs {company.index_name}</h2>
        {prices ? (
          <PriceChart path={prices} benchmarkName={company.index_name}
                      stages={assessment.stages.map((s) => ({ day: s.published_at.slice(0, 10), label: title(s.stage_name) }))} />
        ) : <p className="muted">No price data connected yet, so the share price can't be shown.</p>}
      </div>
      <div className="overview-cards">
        <div className="card">
          <h3 className="card-kicker">Watch next</h3>
          {card.next_update && <p className="next-update">→ <b>{card.next_update}</b> <span className="muted small">usually comes next</span></p>}
          <ul className="watch-chips">{card.watch.slice(0, 3).map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
        {lead && (
          <div className="card">
            <h3 className="card-kicker">What research shows</h3>
            <p className="research">{lead.finding}</p>
            <p className="cite">{lead.source}</p>
            {more.length > 0 && (
              <details className="more-research">
                <summary className="small">{more.length} more finding{more.length > 1 ? "s" : ""}</summary>
                {more.map((r) => <div key={r.finding}><p className="research small">{r.finding}</p><p className="cite">{r.source}</p></div>)}
              </details>
            )}
          </div>
        )}
      </div>
    </>
  );
}
