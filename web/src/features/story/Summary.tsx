// The conclusion, as one fact per workflow step, then what to watch next.
import { CONFIDENCE, describe, STATUS } from "../../shared/labels";
import { StepBadge } from "../../shared/steps";
import { Card, Pill } from "../../shared/ui";
import type { StoryData } from "./context";

export function Summary({ story, assessment: a }: StoryData) {
  const outlets = new Set(a.stages.flatMap((s) => s.claim.outlets)).size;
  const verified = a.stages.filter((s) => s.claim.status !== "single_source").length;
  const predictions = a.stages.flatMap((s) => s.decisions);
  const tested = predictions.filter((d) => ["consistent", "inconsistent", "not_significant"].includes(d.verdict));
  const happened = tested.filter((d) => d.verdict === "consistent").length;
  const prices = predictions.map((d) => d.evidence).filter((e): e is NonNullable<typeof e> => !!e && e.channel === "price");
  const move = a.combined_reaction ?? [...prices].sort((p, q) => Math.abs(q.statistic ?? 0) - Math.abs(p.statistic ?? 0))[0];
  const conf = CONFIDENCE[a.confidence];
  const facts = [
    { id: "monitor" as const, value: `${outlets} outlet${outlets === 1 ? "" : "s"}`, note: `reported this story; ${verified} of ${a.stages.length} events verified by independent sources` },
    { id: "connect" as const, value: `${a.stages.length} event${a.stages.length === 1 ? "" : "s"}`, note: `linked into one story · ${STATUS[story.status]?.text.toLowerCase() ?? story.status}` },
    { id: "anticipate" as const, value: `${predictions.length} reactions`, note: "predicted for investors, analysts, boards and customers" },
    { id: "verify" as const, value: tested.length ? `${happened} of ${tested.length} happened` : "not tested yet",
      note: move ? `share price ${describe(move)}${move.significant ? " - a clear move" : " - within normal swings"}` : "waiting for market data" },
  ];
  return (
    <Card className="summary">
      <div className="summary-grid">
        {facts.map((f) => (
          <div key={f.id} className={`summary-fact step-${f.id}`}>
            <StepBadge id={f.id} />
            <div className="fact-value">{f.value}</div>
            <div className="fact-sub">{f.note}</div>
          </div>
        ))}
      </div>
      <div className="summary-verdict">
        {conf && <Pill tone={conf.tone}>{conf.text}</Pill>}
        <span className="muted small">Confidence is high only when the events are verified by independent sources and the market confirmed most predicted reactions.</span>
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
