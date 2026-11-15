// Small presentational building blocks shared by every feature.
import type { ReactNode } from "react";
import type { Tone } from "./labels";

export function Pill({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`pill ${tone}`}>{children}</span>;
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function Section({ title, hint, children }: { title: string; hint?: ReactNode; children: ReactNode }) {
  return (
    <section className="section">
      <div className="section-head">
        <h2>{title}</h2>
        {hint && <p className="muted">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

export function Fact({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: Tone }) {
  return (
    <div className="fact">
      <div className="fact-label">{label}</div>
      <div className={`fact-value ${tone ?? ""}`}>{value}</div>
      {sub && <div className="fact-sub">{sub}</div>}
    </div>
  );
}

export function State({ error, loading, empty, children }: {
  error?: string | null; loading?: boolean; empty?: ReactNode; children?: ReactNode;
}) {
  if (error) return <p className="state error">Something went wrong: {error}</p>;
  if (loading) return <p className="state muted">Loading…</p>;
  if (empty) return <div className="state empty">{empty}</div>;
  return <>{children}</>;
}
