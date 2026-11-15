// The chart and what to do about it: the two things most readers came for.
import { useNames } from "../../shared/names";
import { PriceChart } from "../../shared/PriceChart";
import type { EventData } from "./context";

export function Overview({ company, card, assessment, prices }: EventData) {
  const { title } = useNames();
  return (
    <div className="overview">
      <div className="card">
        <h2>Share price vs {company.index_name}</h2>
        {prices ? (
          <PriceChart path={prices} benchmarkName={company.index_name}
                      stages={assessment.stages.map((s) => ({ day: s.published_at.slice(0, 10), label: title(s.stage_name) }))} />
        ) : <p className="muted">No price data connected yet, so the share price can't be shown.</p>}
      </div>
      <div className="card actions">
        <h2>Suggested actions</h2>
        <ol className="action-list">{card.actions.map((x) => <li key={x}>{x}</li>)}</ol>
        <p className="small muted">{assessment.disclaimer}</p>
      </div>
    </div>
  );
}
