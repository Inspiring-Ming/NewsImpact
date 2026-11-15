// The ONE place for wording shown to people. Plain words, as a newspaper or a
// broker's watchlist would use them. Story and event names come from
// data/reference/playbooks.json and outlet names from sources.json (see names.ts).
import type { S } from "../api/client";

const NAMES: Record<string, string> = {
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

export const COUNTRY: Record<string, { flag: string; name: string }> = {
  US: { flag: "🇺🇸", name: "United States" }, AU: { flag: "🇦🇺", name: "Australia" },
  TW: { flag: "🇹🇼", name: "Taiwan" }, GB: { flag: "🇬🇧", name: "United Kingdom" },
};

export const STATUS_TONE: Record<string, Tone> = { unfolding: "ok", escalating: "bad", settled: "neutral" };
export const CONFIRMED_TONE: Record<string, Tone> = { yes: "good", partly: "ok", no: "warn" };
export const EVIDENCE: Record<string, { text: string; tone: Tone }> = {
  strong: { text: "Strong evidence", tone: "good" },
  partial: { text: "Partial evidence", tone: "ok" },
  weak: { text: "Weak evidence", tone: "warn" },
};

/** Did the predicted reaction happen? */
export const RESULT: Record<string, { text: string; tone: Tone }> = {
  consistent: { text: "Yes", tone: "good" },
  inconsistent: { text: "No - the opposite", tone: "bad" },
  not_significant: { text: "No clear reaction", tone: "neutral" },
  pending: { text: "Too early to tell", tone: "neutral" },
  no_evidence: { text: "No data yet", tone: "muted" },
  not_measurable: { text: "Not visible in prices", tone: "muted" },
};

export const DIRECTION: Record<string, string> = { up: "rise", down: "fall", uncertain: "move sharply" };

/** "18.5% below the S&P 500", "3.7× normal trading volume" ... */
export function describe(o: S["ChannelObservation"], benchmark = "market"): string {
  if (o.channel === "price") return `${Math.abs(o.value * 100).toFixed(1)}% ${o.value < 0 ? "below" : "above"} the ${benchmark}`;
  if (o.channel === "volume") return `${o.value.toFixed(1)}× normal trading volume`;
  if (o.channel === "volatility") return `${o.value.toFixed(1)}× normal price swings`;
  return `${o.metric} = ${o.value}`;
}

export function date(iso: string, year = false): string {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", ...(year ? { year: "numeric" } : {}) });
}
