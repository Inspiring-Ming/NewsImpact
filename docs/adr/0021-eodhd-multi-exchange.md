# 0021 – EODHD for prices; each stock measured on its home exchange

* Status: accepted (supersedes the vendor choice in 0019)
* Date: 2026-11-15

## Context
We watch US and Australian (ASX) companies. Validation needs adjusted daily
prices for both, retrieved automatically and affordably, with rights to show
results to clients later. Each stock reacts on its own exchange's session.

## Decision
* **EODHD** end-of-day data, one feed for US and ASX:
  * adjusted closes;
  * a stated official ASX redistribution licence;
  * about $19.99/month for the end-of-day plan, and a free development tier
    of 20 calls/day for personal use.
  * The Tiingo adapter is removed.
* EODHD takes its key in the URL, so adapter errors are re-raised without
  the URL. The SQLite cache keeps calls to about one per company per day.
* Per-exchange rules live in `methodology.json` → market:
  * time zone, 16:00 close, benchmark (US: SPY, ASX: STW) and vendor code;
  * ASX tickers end in `.AX`;
  * after-close news moves to the next session of the *home* exchange.

## Consequences
+ One vendor and one adapter cover both markets. Adding a market is a data
  change.
− A client product needs EODHD's commercial licence, which is priced
  separately and not verified here. Re-check prices before budgeting.
