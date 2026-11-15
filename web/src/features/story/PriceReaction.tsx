// The share price against its market, with each event marked.
import { useNames } from "../../shared/names";
import { PriceChart } from "../../shared/PriceChart";
import { Card } from "../../shared/ui";
import type { StoryData } from "./context";

export function PriceReaction({ assessment, prices, company, card }: StoryData) {
  const { title } = useNames();
  return (
    <Card>
      <p className="lead-small">{card.reaction_text}.</p>
      {prices ? (
        <PriceChart path={prices} benchmarkName={company.benchmark_name}
                    stages={assessment.stages.map((s) => ({ day: s.published_at.slice(0, 10), label: title(s.stage_name) }))} />
      ) : (
        <p className="muted">No price data connected yet, so the share price can't be shown.</p>
      )}
    </Card>
  );
}
