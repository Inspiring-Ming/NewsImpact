// The ONE place that turns internal codes into plain English.
// New event types, stages or channels work without changes (humanize fallback);
// add an entry here only to give something a nicer name.
import type { S } from "../api/client";

const NAMES: Record<string, string> = {
  // storyline types
  leadership_crisis: "Leadership crisis", product_safety: "Product safety", m_and_a: "Deal (M&A)",
  // stages
  public_pressure: "Public pressure", leader_departure: "Leader steps down", succession: "Successor named",
  recall: "Product recall", regulatory_action: "Regulator acts", litigation: "Lawsuit",
  rumour: "Deal rumour", announcement: "Deal announced",
  // market channels
  price: "Share price", volume: "Trading volume", volatility: "Volatility",
  analyst_revisions: "Analyst forecasts", credit_spreads: "Credit spreads", peer_spillover: "Competitors",
  // statuses
  developing: "Developing", escalating: "Escalating", resolved: "Resolved",
};

export function label(code: string): string {
  return NAMES[code] ?? humanize(code);
}

export function humanize(code: string): string {
  const s = code.replace(/[_-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export type Tone = "good" | "ok" | "warn" | "bad" | "neutral" | "muted";

export const VERDICT: Record<string, { text: string; tone: Tone }> = {
  consistent: { text: "As expected", tone: "good" },
  inconsistent: { text: "Opposite of expected", tone: "bad" },
  not_significant: { text: "No clear move", tone: "neutral" },
  pending: { text: "Waiting for data", tone: "neutral" },
  no_evidence: { text: "No data source yet", tone: "muted" },
  not_measurable: { text: "Not visible in markets", tone: "muted" },
};

export const CLAIM: Record<string, { text: string; tone: Tone }> = {
  confirmed: { text: "Confirmed", tone: "good" },
  corroborated: { text: "Corroborated", tone: "ok" },
  single_source: { text: "Single source", tone: "warn" },
};

export const CONFIDENCE: Record<string, { text: string; tone: Tone }> = {
  high: { text: "High confidence", tone: "good" },
  medium: { text: "Medium confidence", tone: "ok" },
  low: { text: "Low confidence", tone: "warn" },
};

export const STATUS_TONE: Record<string, Tone> = { developing: "ok", escalating: "bad", resolved: "neutral" };

export const EXPECTED: Record<string, string> = { up: "rise", down: "fall", uncertain: "move" };

/** "−5.3% vs market", "2.0× normal volume" ... */
export function describe(o: S["ChannelObservation"]): string {
  if (o.channel === "price") return `${signedPct(o.value)} vs market`;
  if (o.channel === "volume") return `${o.value.toFixed(1)}× normal trading`;
  if (o.channel === "volatility") return `${o.value.toFixed(1)}× normal volatility`;
  return `${o.metric} = ${o.value}`;
}

export function signedPct(x: number, digits = 1): string {
  return `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toFixed(digits)}%`;
}

export function date(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}
