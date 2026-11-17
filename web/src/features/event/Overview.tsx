// Overview, in the order a professional reads it: the brief (what happened, what the
// market did, why it matters), what to check now, the price chart, then context: this
// event type's track record, what to watch, and what published research shows.
import { useState } from "react";
import { CHANCE_WORDS, EXPECT, pct, verdictText } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { PriceChart } from "../../shared/PriceChart";
import { Term } from "../../shared/Term";
import { MoveBar } from "../../shared/viz";
import type { EventData } from "./context";

const BRIEF_LABELS = ["What happened", "What the market did", "Why it matters"];

export function Overview({ company, card, assessment, prices }: EventData) {
  const { title } = useNames();
  const [done, setDone] = useState<Set<number>>(new Set());
  const [lead, ...more] = card.research;
  const past = card.record, expected = card.expectation;
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
        {expected && (
          <div className="card">
            <h3 className="card-kicker">Expected for this case</h3>
            <p><b>{expected.label[0].toUpperCase() + expected.label.slice(1)}</b>: research expects the share price <span className={`expect ${EXPECT[expected.expected].tone}`}>{EXPECT[expected.expected].text}</span>.</p>
            <p className="small muted">{expected.finding} <i>{expected.source}</i></p>
            {past && past.n > 0 && past.average != null ? (
              <>
                <div className="move-top"><b className="big-num">{pct(past.average)}</b><MoveBar value={past.average} unusual={false} span={0.1} /></div>
                <p className="small"><b>{past.met} of {past.n}</b> past events in this case {EXPECT[past.expected].did} (by chance alone: {CHANCE_WORDS[past.expected]}), average move above.</p>
                <span className={`verdict ${verdictText(past).tone}`}>{verdictText(past).text}</span>
              </>
            ) : <p className="small muted">No past event in this case measured yet.</p>}
          </div>
        )}
        <div className="card">
          <h3 className="card-kicker">Watch next</h3>
          {card.next_update && <p className="next-update">→ <b>{card.next_update}</b> <span className="muted small">possible next step (from research; may not happen)</span></p>}
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
