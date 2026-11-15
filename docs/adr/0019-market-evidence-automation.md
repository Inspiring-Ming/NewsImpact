# 0019 – Automated, reproducible market evidence

* Status: accepted (vendor: see 0021)
* Date: 2026-11-15

## Context
Validating decisions needs real prices, retrieved automatically and measured
the same way every time. The free CSV source we tried (Stooq) now blocks
scripted access, and unofficial scrapers are not licensed for products.

## Decision
* Market data is a port with adapters:
  * Tiingo end-of-day (API key in a header, adjusted prices);
  * CSV exports from any licensed vendor (reproducible snapshots);
  * the synthetic demo data.
  A SQLite cache wraps any of them.
* Measurement follows `methodology.json`:
  * windows per channel, an estimation window and a significance level;
  * the 16:00 New York close, so after-close news counts from the next
    trading day.
* Windows not yet finished return "pending". Each monitoring round
  re-assesses storylines and stores assessments when they change, so
  evidence matures on its own.
* Across storylines, `calibrate` runs the BMP cross-sectional test per stage
  and channel.

## Consequences
+ No manual step between news, price retrieval and evaluation.
+ Reproducible: CSV snapshots, a hashed methodology and provider versions in
  provenance.
− The live profile has no market evidence until a vendor is chosen. The
  vendor's commercial terms and cost must be checked before client use; they
  were not verified here.
