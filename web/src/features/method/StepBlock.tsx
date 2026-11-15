// One workflow step explained the same way every time: what we do, the rule, the evidence.
import type { ReactNode } from "react";
import { STEPS, StepBadge, type StepId } from "../../shared/steps";

export function StepBlock({ id, what, rules, children }: {
  id: StepId; what: string; rules: ReactNode[]; children: ReactNode;
}) {
  const step = STEPS.find((s) => s.id === id)!;
  return (
    <section className={`step-block step-${id}`}>
      <div className="step-block-head">
        <StepBadge id={id} />
        <h2>{step.verb}</h2>
      </div>
      <div className="step-block-body">
        <div>
          <h3>What we do</h3>
          <p>{what}</p>
          <h3>The rule</h3>
          <ul className="rules">{rules.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </div>
        <div>
          <h3>The evidence</h3>
          {children}
        </div>
      </div>
    </section>
  );
}
