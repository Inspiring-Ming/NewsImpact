// The ONE place for wording shown to people. Plain words, as a newspaper or a
// broker's watchlist would use them. Event and update names come from
// data/reference/playbooks.json and source names from sources.json (see names.ts).
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

export const SECTORS = [
  "Information Technology", "Communication Services", "Consumer Discretionary", "Consumer Staples",
  "Financials", "Health Care", "Energy", "Materials", "Industrials", "Utilities", "Real Estate",
];

/** Every term a reader may not know, defined once in plain words. Shown on hover by <Term>. */
export const TERMS = {
  sector: { label: "Sector", tip: "The company's industry under GICS (Global Industry Classification Standard), the 11-sector system used by MSCI, S&P and most fund managers." },
  event: { label: "Latest event", tip: "Company news of a kind known to move share prices, e.g. a CEO leaving, a takeover, an earnings miss. An event is a chain of dated updates." },
  move: { label: "Stock vs market", tip: "How much better (+) or worse (−) the stock did than its whole market over the event days (S&P 500 for US, ASX 200 for Australia). Taking out the market's own move leaves the company's reaction to its news." },
  unusual: { label: "Unusual move", tip: "A move this large happens on fewer than 1 in 20 normal days for this stock (judged from its previous 120 trading days), so it is unlikely to be chance." },
  confirmed: { label: "Confirmed", tip: "Reported by 2 or more independent news sources, or published by the company itself (a press release) or in an official filing." },
  single: { label: "Single source", tip: "Only one news source has reported this so far. Treat it as a lead to check, not a fact. It becomes Confirmed when another independent source, the company or a filing reports it." },
  tone: { label: "Tone", tip: "Whether the latest update reads as good or bad news for the company, read automatically from its wording." },
  rumour: { label: "Rumour", tip: "Worded as unconfirmed: 'reportedly', 'is said to', 'sources say', 'considering'. Nobody has confirmed it on the record yet." },
  sources: { label: "Sources", tip: "How many of our news sources reported the event. Copies of the same article count once." },
  reliability: { label: "Reliability", tip: "Chance a report from this source is right. = (starting estimate × 10 + reports confirmed) ÷ (10 + reports judged), where a report nobody else confirmed within 7 days counts as half a miss. So a source starts at its type's estimate and moves with its own record." },
  prior: { label: "Starting estimate", tip: "Set by the kind of source, ordered by how content is checked before publishing: official filing 95% (legal liability), news agency 80% and newspaper 75% (editors, corrections policy), company press release 67% (accurate about itself but selective), news aggregator 67% (mixes reporting and opinion). It counts as much as 10 reports, then the track record takes over." },
  trackRecord: { label: "Track record", tip: "Of this source's reports old enough to judge (7+ days), how many another independent source also reported. Sources whose news others confirm are more trustworthy (truth-discovery research: Yin, Han & Yu 2008)." },
  accuracy: { label: "How accurately we read the news", tip: "Before trusting the automatic reading, we test it: 56 real news sentences were labelled by hand (which event, who said it, rumour or fact, new or old news) and we count how often our reading matches. If a change makes these scores drop, it is not released." },
  provisional: { label: "Provisional", tip: "The measurement window has not closed yet, so this is the stock's move against its index up to the latest close. It can still change; the final number replaces it once the window closes." },
  eventsWeek: { label: "Events this week", tip: "Events with a new update in the last 7 days." },
  biggest: { label: "Biggest move", tip: "The largest stock move against its market among all events." },
  news24h: { label: "News in 24 hours", tip: "Articles our sources published in the last 24 hours." },
  map: { label: "Impact map", tip: "Every event with a measured stock move. Left = the stock did worse than its market, right = better. Rows are sectors. Bigger dot = more sources. Click a dot to open the event." },
  volume: { label: "Trading volume", tip: "Shares traded compared with this stock's normal day, over the update day and the 2 days after." },
  expected: { label: "Expected vs actual", tip: "For each update: the reaction investors usually show (↑ rise, ↓ fall, ↕ big move either way) and what really happened (✓ as expected, ✗ the opposite, – no clear move)." },
  relevance: { label: "About our companies", tip: "Share of this source's articles that name a company we follow. Low = the source mostly covers other things, so it adds little." },
  usedInEvent: { label: "Led to an event", tip: "Share of this source's articles that became an update of an event. Shows whether the source reports the news that matters." },
  window: { label: "Time window", tip: "A new report within this many days of the last update joins the same event; after that it starts a new event. Set from typical timelines, then checked against the gaps we measure." },
  seen: { label: "Measured gap", tip: "Typical number of days between updates of this event type, measured from our own data." },
  expectShare: { label: "Expected share price", tip: "What research on investor behaviour says this kind of news usually does to the share price." },
  measured: { label: "Events measured", tip: "Events of this type with a completed stock measurement." },
  avgMove: { label: "Average move", tip: "Average stock move against its market across those events." },
  asExpected: { label: "Moved as expected", tip: "Events where the share price went the expected way (for 'big move either way': an unusual move). This is how we check that the expectation holds in real data." },
  sourcesTab: { label: "Which news sources we read", tip: "We read a short list of trusted sources automatically. Each keeps its place only if it covers our companies and leads to events." },
  eventsTab: { label: "Which events we detect", tip: "Each sentence naming a company is checked for an event type. Related news about the same company within the time window is joined into one event, update by update." },
  marketTab: { label: "Does this news move the stock?", tip: "For each event type: what we expect the share price to do, and what really happened in the events measured so far." },
} as const;

/** GICS sector short names, as on trading screens. */
export const SECTOR_SHORT: Record<string, string> = {
  "Information Technology": "IT", "Communication Services": "Comm Svcs", "Consumer Discretionary": "Cons Disc",
  "Consumer Staples": "Cons Staples", Financials: "Financials", "Health Care": "Health Care", Energy: "Energy",
  Materials: "Materials", Industrials: "Industrials", Utilities: "Utilities", "Real Estate": "Real Estate",
};

/** Tone of the wording, for the company: thresholds keep near-zero scores neutral. */
export function tone(x: number): { text: string; icon: string; tone: Tone } {
  if (x <= -0.15) return { text: "Bad news", icon: "▼", tone: "bad" };
  if (x >= 0.15) return { text: "Good news", icon: "▲", tone: "good" };
  return { text: "Neutral", icon: "●", tone: "neutral" };
}

/** "−18.5%" with a sign, for stock moves against an index. */
export function pct(x: number, digits = 1): string {
  return `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toFixed(digits)}%`;
}

/** Did the predicted reaction happen? */
export const RESULT: Record<string, { text: string; icon: string; tone: Tone }> = {
  consistent: { text: "As expected", icon: "✓", tone: "good" },
  inconsistent: { text: "Opposite of expected", icon: "✗", tone: "bad" },
  not_significant: { text: "No clear move", icon: "–", tone: "neutral" },
  pending: { text: "Too early to tell", icon: "…", tone: "neutral" },
  no_evidence: { text: "No data yet", icon: "?", tone: "muted" },
  not_measurable: { text: "Not visible in prices", icon: "·", tone: "muted" },
};

/** "worse than the S&P 500" - the sign of a move against its index, in words. */
export function vsWords(x: number, index: string): string {
  return `${x < 0 ? "worse" : "better"} than the ${index}`;
}

/** "18.5% worse than the S&P 500" */
export function moveVs(x: number, index: string): string {
  return `${Math.abs(x * 100).toFixed(1)}% ${vsWords(x, index)}`;
}

/** Why a stock move is not shown yet. */
export const NO_MOVE: Record<string, string> = {
  pending: "Too early: check after the next trading day",
  no_data: "No price data yet",
};

export const ARROW: Record<string, string> = { up: "↑", down: "↓", uncertain: "↕" };


/** "18.5% worse than the S&P 500", "3.7× normal trading volume" ... */
export function describe(o: S["ChannelObservation"], benchmark = "market"): string {
  if (o.channel === "price") return moveVs(o.value, benchmark);
  if (o.channel === "volume") return `${o.value.toFixed(1)}× normal trading volume`;
  if (o.channel === "volatility") return `${o.value.toFixed(1)}× normal price swings`;
  return `${o.metric} = ${o.value}`;
}

export function date(iso: string, year = false): string {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", ...(year ? { year: "numeric" } : {}) });
}
