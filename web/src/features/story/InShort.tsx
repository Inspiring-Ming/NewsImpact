// "In short": the three facts a reader needs, then our conclusion and what to watch.
import { CONFIDENCE, describe } from "../../shared/labels";
import { Card, Fact } from "../../shared/ui";
import type { StoryData } from "./context";

export function InShort({ assessment: a }: StoryData) {
  const confirmed = a.stages.filter((s) => s.claim.status !== "single_source").length;
  const measured = a.stages.flatMap((s) => s.decisions)
    .filter((d) => ["consistent", "inconsistent", "not_significant"].includes(d.verdict));
  const met = measured.filter((d) => d.verdict === "consistent").length;
  const prices = a.stages.flatMap((s) => s.decisions).map((d) => d.evidence)
    .filter((e): e is NonNullable<typeof e> => !!e && e.channel === "price");
  const headline = a.combined_reaction ?? prices.sort((p, q) => Math.abs(q.statistic ?? 0) - Math.abs(p.statistic ?? 0))[0];
  const conf = CONFIDENCE[a.confidence];
  return (
    <Card className="in-short">
      <div className="facts">
        <Fact label="Did it really happen?" value={`${confirmed} of ${a.stages.length} stages confirmed`}
              sub="by independent outlets, the company or a filing" tone={confirmed === a.stages.length ? "good" : "warn"} />
        <Fact label="What did the market do?" value={headline ? describe(headline) : "not measured yet"}
              sub={headline ? (headline.significant ? "a clear move, beyond normal days" : "within normal day-to-day noise") : "connect price data"}
              tone={headline?.significant ? (headline.value < 0 ? "bad" : "good") : undefined} />
        <Fact label="Did people act as expected?" value={measured.length ? `${met} of ${measured.length} expectations met` : "—"}
              sub="checked against market data" />
        <Fact label="Overall" value={conf?.text ?? a.confidence} tone={conf?.tone} />
      </div>
      <h3>What to watch</h3>
      <ul className="tips">{a.suggestions.slice(0, 3).map((t) => <li key={t}>{t}</li>)}</ul>
      {a.suggestions.length > 3 && (
        <details className="more">
          <summary>{a.suggestions.length - 3} more</summary>
          <ul className="tips">{a.suggestions.slice(3).map((t) => <li key={t}>{t}</li>)}</ul>
        </details>
      )}
      <p className="muted small">{a.disclaimer}</p>
    </Card>
  );
}
