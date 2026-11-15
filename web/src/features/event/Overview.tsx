// Overview: the share price against its market with each update marked, then two short
// cards: what to watch next, and what published research says usually happens.
import { api } from "../../api/client";
import { typeRecord } from "../../shared/history";
import { pct } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { useApi } from "../../shared/useApi";
import { Meter, MoveBar } from "../../shared/viz";
import { PriceChart } from "../../shared/PriceChart";
import type { EventData } from "./context";

export function Overview({ company, card, assessment, prices }: EventData) {
  const { title } = useNames();
  const [lead, ...more] = card.research;
  const method = useApi(api.method);
  const companies = useApi(api.companies);
  const playbook = method.data?.playbooks.find((p) => (p.title || p.theme) === card.event_type);
  const past = playbook && companies.data ? typeRecord(playbook, companies.data.flatMap((c) => c.events)) : null;
  return (
    <>
      <div className="card">
        <h2>Share price vs {company.index_name}</h2>
        {prices ? (
          <PriceChart path={prices} benchmarkName={company.index_name}
                      stages={assessment.stages.map((s) => ({ day: s.published_at.slice(0, 10), label: title(s.stage_name) }))} />
        ) : <p className="muted">No price data connected yet, so the share price can't be shown.</p>}
      </div>
      <div className="overview-cards three">
        {past && (
          <div className="card">
            <h3 className="card-kicker">Past {card.event_type.toLowerCase()} events we measured</h3>
            {past.n ? (
              <>
                <div className="move-top"><b className="big-num">{pct(past.avg!)}</b><MoveBar value={past.avg!} unusual={false} span={0.1} /></div>
                <p className="small muted">average stock move vs its market, over {past.n} event{past.n > 1 ? "s" : ""}</p>
                <div className="conf"><Meter value={past.asExpected / past.n} tone={past.asExpected / past.n >= 0.6 ? "good" : "warn"} />
                  <span className="small">{past.asExpected} of {past.n} moved as expected</span></div>
                {past.n < 20 && <p className="small muted">Few events so far: treat as a first indication, not a rule.</p>}
              </>
            ) : <p className="small muted">None measured yet.</p>}
          </div>
        )}
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
