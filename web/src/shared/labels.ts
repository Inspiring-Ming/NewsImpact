// The ONE place that turns internal codes into plain English, using one small
// vocabulary: story, event, source, predicted reaction, result.
// New codes work without changes (humanize fallback); add entries only for nicer names.
import type { S } from "../api/client";

const NAMES: Record<string, string> = {
  // (story types and events are named in data/reference/playbooks.json - see names.ts)
  // where a reaction shows
  price: "share price", volume: "trading volume", volatility: "price swings",
  analyst_revisions: "analyst forecasts", credit_spreads: "borrowing costs", peer_spillover: "competitors",
  // who reacts
  institutional_investors: "Large investors", retail_investors: "Individual investors",
  sell_side_analysts: "Analysts", options_market: "Options traders", credit_investors: "Bond investors",
  event_driven_funds: "Event-driven funds", customers_partners: "Customers and partners",
  all_investors: "Investors",
};

export function label(code: string): string {
  return NAMES[code] ?? humanize(code);
}

export function humanize(code: string): string {
  const s = code.replace(/[_-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export type Tone = "good" | "ok" | "warn" | "bad" | "neutral" | "muted";

/** Story status in plain words. */
export const STATUS: Record<string, { text: string; tone: Tone }> = {
  developing: { text: "Ongoing", tone: "ok" },
  escalating: { text: "Getting worse", tone: "bad" },
  resolved: { text: "Concluded", tone: "neutral" },
};

/** Did the predicted reaction happen? */
export const RESULT: Record<string, { text: string; tone: Tone }> = {
  consistent: { text: "Happened", tone: "good" },
  inconsistent: { text: "Opposite happened", tone: "bad" },
  not_significant: { text: "No clear reaction", tone: "neutral" },
  pending: { text: "Too early to tell", tone: "neutral" },
  no_evidence: { text: "No data yet", tone: "muted" },
  not_measurable: { text: "Not in market data", tone: "muted" },
};

/** Is the event backed by independent sources? */
export const SOURCES: Record<string, { text: string; tone: Tone }> = {
  confirmed: { text: "Verified", tone: "good" },
  corroborated: { text: "Two sources agree", tone: "ok" },
  single_source: { text: "One source so far", tone: "warn" },
};

export const CONFIDENCE: Record<string, { text: string; tone: Tone }> = {
  high: { text: "High confidence", tone: "good" },
  medium: { text: "Medium confidence", tone: "ok" },
  low: { text: "Low confidence", tone: "warn" },
};

export const DIRECTION: Record<string, string> = { up: "rise", down: "fall", uncertain: "move sharply" };

/** "−5.3% vs market", "2.0× normal trading" ... */
export function describe(o: S["ChannelObservation"]): string {
  if (o.channel === "price") return `${signedPct(o.value)} vs market`;
  if (o.channel === "volume") return `${o.value.toFixed(1)}× normal trading`;
  if (o.channel === "volatility") return `${o.value.toFixed(1)}× normal price swings`;
  return `${o.metric} = ${o.value}`;
}

export function signedPct(x: number, digits = 1): string {
  return `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toFixed(digits)}%`;
}

export function date(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}
