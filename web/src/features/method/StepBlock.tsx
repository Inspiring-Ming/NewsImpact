// One part of the method: a title that explains itself on hover, then the data.
import type { ReactNode } from "react";
import type { TERMS } from "../../shared/labels";
import { Term } from "../../shared/Term";

export function StepBlock({ term, children }: { term: keyof typeof TERMS; children: ReactNode }) {
  return (
    <section className="step-block">
      <h2><Term id={term} /></h2>
      {children}
    </section>
  );
}
