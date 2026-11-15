// The chart and what to know about it: what we measured, what research says usually
// happens next (cited), and what investors check next. Rules from reference data
// (playbooks.json), so every statement can be traced to its source.
import { moveVs } from "../../shared/labels";
import { useNames } from "../../shared/names";
import { PriceChart } from "../../shared/PriceChart";
import type { EventData } from "./context";

export function Overview({ company, card, assessment, prices }: EventData) {
  const { title } = useNames();
  const facts = [
    card.stock_move != null
      ? `The stock did ${moveVs(card.stock_move, company.index_name)} (${card.stock_move_period})${card.stock_move_unusual ? ", an unusual move." : ", within its normal range."}`
      : "The stock reaction is not measured yet.",
    card.volume_ratio != null ? `Trading volume reached ${card.volume_ratio.toFixed(1)}× a normal day.` : null,
    `${card.sources} ${card.sources === 1 ? "source" : "independent sources"} reported it: ${Math.round(card.confidence * 100)}% confidence the news is true.`,
    card.is_rumour ? "The latest update is worded as a rumour, not a confirmed fact." : null,
  ].filter(Boolean) as string[];
  return (
    <div className="overview">
      <div className="card">
        <h2>Share price vs {company.index_name}</h2>
        {prices ? (
          <PriceChart path={prices} benchmarkName={company.index_name}
                      stages={assessment.stages.map((s) => ({ day: s.published_at.slice(0, 10), label: title(s.stage_name) }))} />
        ) : <p className="muted">No price data connected yet, so the share price can't be shown.</p>}
      </div>
      <div className="card know">
        <h2>What to know</h2>
        <h3>What we measured</h3>
        <ul className="know-list">{facts.map((f) => <li key={f}>{f}</li>)}</ul>
        {card.research.length > 0 && (
          <>
            <h3>What research shows usually happens</h3>
            <ul className="know-list">
              {card.research.map((r) => <li key={r.finding}>{r.finding}<div className="cite">{r.source}</div></li>)}
            </ul>
          </>
        )}
        <h3>What to watch next</h3>
        <ul className="know-list watch">
          {card.next_update && <li><b>Next usual update: {card.next_update}</b></li>}
          {card.watch.map((w) => <li key={w}>{w}</li>)}
        </ul>
        <p className="small muted">{assessment.disclaimer}</p>
      </div>
    </div>
  );
}
