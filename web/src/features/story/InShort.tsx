// The four plain answers, and what to watch next.
import { CONFIRMED_TONE, EVIDENCE, STATUS_TONE } from "../../shared/labels";
import { Card, Pill } from "../../shared/ui";
import type { StoryData } from "./context";

export function InShort({ card, assessment: a }: StoryData) {
  const ev = EVIDENCE[card.evidence];
  const moved = card.reaction?.significant;
  return (
    <Card>
      <dl className="answers big">
        <dt>Status</dt>
        <dd><Pill tone={STATUS_TONE[card.status]}>{card.status_text}</Pill></dd>
        <dt>Stock reaction</dt>
        <dd className={moved ? (card.reaction!.value < 0 ? "bad" : "good") : ""}>{card.reaction_text}</dd>
        <dt>News confirmed?</dt>
        <dd><Pill tone={CONFIRMED_TONE[card.confirmed]}>{card.confirmed_text}</Pill></dd>
        <dt>Evidence</dt>
        <dd>{ev && <Pill tone={ev.tone}>{ev.text}</Pill>} <span className="muted small">{card.evidence_text}</span></dd>
      </dl>
      <h3>What to watch next</h3>
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
