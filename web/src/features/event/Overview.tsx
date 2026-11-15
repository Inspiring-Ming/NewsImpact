// Overview, in the order a professional reads it: the brief (what happened, what the
// market did, why it matters), what to check now, the price chart, then context: this
// event type's track record, what to watch, and what published research shows.
import { useState } from "react";
import { pct } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { PriceChart } from "../../shared/PriceChart";
import { Term } from "../../shared/Term";
import { Meter, MoveBar } from "../../shared/viz";
import type { EventData } from "./context";

const BRIEF_LABELS = ["What happened", "What the market did", "Why it matters"];

export function Overview({ company, card, assessment, prices }: EventData) {
  const { title } = useNames();
  const [done, setDone] = useState<Set<number>>(new Set());
  const [lead, ...more] = card.research;
  const past = card.record;
  return (
    <>
      <div className="brief-row">
        <div className="card brief">
          <h3 className="card-kicker">
            Brief · <Term tip={card.brief_by === "ai"
              ? "Written by a language model from the facts on this page only, then checked: no buy, sell or hold wording, and no number that is not in our data."
              : "Written by fixed rules from the facts on this page."}>{card.brief_by === "ai" ? "written by AI from our data" : "from our data"}</Term>
          </h3>
          <dl className="brief-lines">
            {card.brief.map((line, i) => (
              <div key={i}><dt>{BRIEF_LABELS[i]}</dt><dd>{line}</dd></div>
            ))}
          </dl>
        </div>
        <div className="card checklist">
          <h3 className="card-kicker">What to check now</h3>
          <ul>
            {card.checks.map((c, i) => (
              <li key={c.text} className={done.has(i) ? "done" : ""}>
                <label>
                  <input type="checkbox" checked={done.has(i)}
                         onChange={() => { const n = new Set(done); if (n.has(i)) n.delete(i); else n.add(i); setDone(n); }} />
                  <span>{c.url ? <a href={c.url} target="_blank" rel="noreferrer">{c.text} ↗</a> : c.text}</span>
                </label>
              </li>
            ))}
          </ul>
          <p className="small muted">Facts to check, not advice to buy or sell.</p>
        </div>
      </div>
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
            {past.n && past.average != null ? (
              <>
                <div className="move-top"><b className="big-num">{pct(past.average)}</b><MoveBar value={past.average} unusual={false} span={0.1} /></div>
                <p className="small muted">average stock move vs its market, over {past.n} event{past.n > 1 ? "s" : ""}</p>
                <div className="conf"><Meter value={past.as_expected / past.n} tone={past.as_expected / past.n >= 0.6 ? "good" : "warn"} />
                  <span className="small">{past.as_expected} of {past.n} moved as expected</span></div>
                {past.n < 20 && <p className="small muted">Few events so far: a first indication, not a rule.</p>}
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
