// One part of the method, explained the same way every time: what we do, the rule, the evidence.
import type { ReactNode } from "react";

export function StepBlock({ title, term, what, rules, children }: {
  title: string; term: string; what: string; rules: ReactNode[]; children: ReactNode;
}) {
  return (
    <section className="step-block">
      <h2>{title}</h2>
      <p className="muted small">Also known as: {term}</p>
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
