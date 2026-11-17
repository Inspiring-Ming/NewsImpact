// The ONE place for wording shown to people. Plain words, as a newspaper or a
// broker's watchlist would use them. Event and update names come from
// data/reference/playbooks.json and source names from sources.json (see names.ts).

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

// An event's kind, with its reading when it can go either way: "Results · worse than expected".
export function eventLabel(e: { event_type: string; reading?: string | null }): string {
  return e.reading ? `${e.event_type} · ${e.reading}` : e.event_type;
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
  single: { label: "Not yet confirmed", tip: "Only one news source has reported this so far. Treat it as a lead to check, not a fact. It becomes Confirmed when another independent source, the company itself or an official filing reports it." },
  tone: { label: "Tone", tip: "Whether the latest update reads as good or bad news for the company, read automatically from its wording." },
  rumour: { label: "Rumour", tip: "Worded as unconfirmed: 'reportedly', 'is said to', 'sources say', 'considering'. Nobody has confirmed it on the record yet." },
  sources: { label: "Sources", tip: "How many of our news sources reported the event. Copies of the same article count once." },
  provisional: { label: "Provisional", tip: "The measurement window has not closed yet, so this is the stock's move against its index up to the latest close. It can still change; the final number replaces it once the window closes." },
  eventsWeek: { label: "Events this week", tip: "Events with a new update in the last 7 days." },
  biggest: { label: "Biggest move", tip: "The largest stock move against its market among all events." },
  news24h: { label: "News in 24 hours", tip: "Articles our sources published in the last 24 hours." },
  map: { label: "Impact map", tip: "Every event with a measured stock move. Left = the stock did worse than its market, right = better. Rows are sectors. Bigger dot = more sources. Click a dot to open the event." },
  volume: { label: "Trading volume", tip: "Shares traded compared with this stock's normal day, over the update day and the 2 days after." },
  expected: { label: "Expected vs actual", tip: "For each update: the reaction investors usually show (↑ rise, ↓ fall, ↕ big move either way) and what really happened (✓ as expected, ✗ the opposite, – no clear move)." },
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

export const ARROW: Record<string, string> = { up: "↑", down: "↓", uncertain: "↕", flat: "→" };

/** What research expects the share price to do, and how a matching event is described. */
export const EXPECT: Record<string, { text: string; did: string; tone: string }> = {
  up: { text: "↑ rises", did: "rose", tone: "good" },
  down: { text: "↓ falls", did: "fell", tone: "bad" },
  flat: { text: "→ little change", did: "had no unusual move", tone: "neutral" },
  uncertain: { text: "↕ a larger move than usual", did: "had an unusual move", tone: "warn" },
};

/** How often each expectation is met by chance alone (server: guidance.py CHANCE). */
export const CHANCE_WORDS: Record<string, string> = {
  up: "1 in 2", down: "1 in 2", uncertain: "1 in 20", flat: "19 in 20",
};

/** The verdict on a case's record against research (server: views/guidance.py group_record). */
export function verdictText(r: { verdict: string }, minEvents?: number): { text: string; tone: string } {
  return {
    too_few: { text: `Too few events to judge${minEvents ? ` (needs ${minEvents})` : " yet"}`, tone: "neutral" },
    supports: { text: "Matches the research", tone: "good" },
    no_pattern: { text: "No clear pattern yet", tone: "warn" },
    against: { text: "Goes against the research", tone: "bad" },
  }[r.verdict] ?? { text: r.verdict, tone: "neutral" };
}



export function date(iso: string, year = false): string {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", ...(year ? { year: "numeric" } : {}) });
}
