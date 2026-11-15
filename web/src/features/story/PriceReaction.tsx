// The share price against its market, with each stage marked.
import { label } from "../../shared/labels";
import { PriceChart } from "../../shared/PriceChart";
import { Card } from "../../shared/ui";
import type { StoryData } from "./context";

export function PriceReaction({ assessment, prices }: StoryData) {
  return (
    <Card>
      {prices ? (
        <PriceChart path={prices} stages={assessment.stages.map((s) => ({ day: s.published_at.slice(0, 10), label: label(s.stage_name) }))} />
      ) : (
        <p className="muted">Price data is not connected yet, so the market reaction can't be shown.</p>
      )}
    </Card>
  );
}
