// Small presentational building blocks shared by every feature.
import { useEffect, useState, type ReactNode } from "react";
import type { Tone } from "./labels";
import { useCountUp } from "./useCountUp";

/** A key number that counts up when shown (see useCountUp). */
export function CountUp({ value }: { value: ReactNode }) {
  return <>{useCountUp(value)}</>;
}

export function Fact({ label, value, sub, tone }: { label: ReactNode; value: ReactNode; sub?: ReactNode; tone?: Tone }) {
  return (
    <div className="fact">
      <div className="fact-label">{label}</div>
      <div className={`fact-value ${tone ?? ""}`}><CountUp value={value} /></div>
      {sub && <div className="fact-sub">{sub}</div>}
    </div>
  );
}

export function State({ error, loading, empty, children }: {
  error?: string | null; loading?: boolean; empty?: ReactNode; children?: ReactNode;
}) {
  if (error) return <p className="state error">Something went wrong: {error}</p>;
  if (loading) return <Skeleton />;
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

/** Shimmering placeholders while data loads: the layout appears at once, then fills in. */
function Skeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="skeleton" role="status" aria-label="Loading">
      <div className="sk-row sk-cards">{[0, 1, 2, 3].map((i) => <span key={i} className="sk-block" />)}</div>
      {Array.from({ length: rows }, (_, i) => <span key={i} className="sk-line" style={{ width: `${92 - i * 9}%` }} />)}
    </div>
  );
}

type Theme = "system" | "light" | "dark";
const THEME_KEY = "newsimpact-theme"; // per-browser preference only

/** Light, dark, or the system's choice; remembered in this browser (if storage is allowed). */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => {
    try { return (localStorage.getItem(THEME_KEY) as Theme | null) ?? "system"; } catch { return "system"; }
  });
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") delete root.dataset.theme; else root.dataset.theme = theme;
    try { if (theme === "system") localStorage.removeItem(THEME_KEY); else localStorage.setItem(THEME_KEY, theme); } catch { /* storage blocked */ }
  }, [theme]);
  const next: Record<Theme, Theme> = { system: "light", light: "dark", dark: "system" };
  const icon = { system: "◐", light: "☀", dark: "☾" }[theme];
  return (
    <button type="button" className="theme-toggle" onClick={() => setTheme(next[theme])}
            aria-label={`Theme: ${theme}. Switch to ${next[theme]}`} title={`Theme: ${theme} (click for ${next[theme]})`}>
      <span aria-hidden="true">{icon}</span>
    </button>
  );
}
