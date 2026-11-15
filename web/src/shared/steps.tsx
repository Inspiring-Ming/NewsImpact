// The product's workflow - the backbone of the whole site. Every page shows the
// same four steps with the same number, colour and words. To add a step, add it here.
import type { ReactNode } from "react";

export type StepId = "monitor" | "connect" | "anticipate" | "verify";

export const STEPS: { id: StepId; n: number; name: string; verb: string }[] = [
  { id: "monitor", n: 1, name: "Monitor", verb: "We read trusted news outlets" },
  { id: "connect", n: 2, name: "Connect", verb: "We link related news into stories" },
  { id: "anticipate", n: 3, name: "Anticipate", verb: "We predict how people will react" },
  { id: "verify", n: 4, name: "Verify", verb: "We check what really happened" },
];

export function StepBadge({ id, withName = true }: { id: StepId; withName?: boolean }) {
  const s = STEPS.find((x) => x.id === id)!;
  return (
    <span className={`step-badge step-${id}`}>
      <span className="step-n">{s.n}</span>{withName && s.name}
    </span>
  );
}

export function StepTitle({ id, title, hint }: { id: StepId; title: string; hint?: ReactNode }) {
  return (
    <div className="step-title">
      <StepBadge id={id} />
      <h2>{title}</h2>
      {hint && <p className="muted">{hint}</p>}
    </div>
  );
}
