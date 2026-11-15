// One part of the method, laid out the same way every time: the rule, then the data behind it.
import type { ReactNode } from "react";

export function StepBlock({ title, term, rules, children }: {
  title: string; term: string; rules: ReactNode[]; children: ReactNode;
}) {
  return (
    <section className="step-block">
      <h2>{title}</h2>
      <p className="muted small">Research term: {term}</p>
      <div className="step-block-body">
        <div>
          <h3>How we decide</h3>
          <ul className="rules">{rules.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </div>
        <div>
          <h3>The data</h3>
          {children}
        </div>
      </div>
    </section>
  );
}
