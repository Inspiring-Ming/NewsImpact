// Small presentational building blocks shared by all pages.
import type { ReactNode } from "react";

export function Page({ title, intro, actions, children }: {
  title: string; intro?: ReactNode; actions?: ReactNode; children: ReactNode;
}) {
  return (
    <section className="page">
      <header className="page-head">
        <div>
          <h1>{title}</h1>
          {intro && <p className="intro">{intro}</p>}
        </div>
        {actions && <div className="actions">{actions}</div>}
      </header>
      {children}
    </section>
  );
}

export function Loading({ error, loading }: { error: string | null; loading: boolean }) {
  if (error) return <p className="error">Could not load: {error}</p>;
  if (loading) return <p className="muted">Loading…</p>;
  return null;
}

export function Card({ title, children, wide }: { title?: string; children: ReactNode; wide?: boolean }) {
  return (
    <div className={wide ? "card wide" : "card"}>
      {title && <h2>{title}</h2>}
      {children}
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

const TONE: Record<string, string> = {
  confirmed: "good", corroborated: "ok", single_source: "warn",
  consistent: "good", inconsistent: "bad", not_significant: "neutral", pending: "neutral",
  no_evidence: "muted", not_measurable: "muted",
  high: "good", medium: "ok", low: "warn",
  resolved: "neutral", escalating: "bad", developing: "ok",
  supported: "good", contradicted: "bad", indicative: "neutral", no_data: "muted",
};

export function Badge({ value }: { value: string }) {
  return <span className={`badge ${TONE[value] ?? "neutral"}`}>{value.replace(/_/g, " ")}</span>;
}

export function pct(x: number | null | undefined, digits = 0): string {
  return x == null ? "–" : `${(x * 100).toFixed(digits)}%`;
}

export function num(x: number | null | undefined, digits = 2): string {
  return x == null ? "–" : x.toFixed(digits);
}

export function day(iso: string): string {
  return iso.slice(0, 10);
}
