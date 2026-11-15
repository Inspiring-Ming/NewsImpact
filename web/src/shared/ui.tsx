// Small presentational building blocks shared by every feature.
import type { ReactNode } from "react";
import type { Tone } from "./labels";

export function Fact({ label, value, sub, tone }: { label: ReactNode; value: ReactNode; sub?: ReactNode; tone?: Tone }) {
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

export function Tabs<T extends string>({ tabs, active, onChange }: {
  tabs: { id: T; label: string }[]; active: T; onChange: (id: T) => void;
}) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={t.id === active}
                className={t.id === active ? "tab active" : "tab"} onClick={() => onChange(t.id)}>
          {t.label}
        </button>
      ))}
    </div>
  );
}
