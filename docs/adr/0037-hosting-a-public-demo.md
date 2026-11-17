# 0037 – Hosting a public demo: visitors read, the owner changes

* Status: accepted
* Date: 2026-11-17

## Context
The product will be put online as a demo before accounts (Cognito) exist. Checked what a
public address changes:
* With `NI_AUTH=local` every visitor is the administrator: anyone could run rounds (AI and
  news requests cost money), load data, or send test alerts to the owner's Discord.
* Starred companies are shared and always followed (ADR 0036): visitors starring companies
  would change what everyone sees and raise the AI cost.
* Every page request re-read and re-checked the ~0.5 MB snapshot, and sent it uncompressed.
* A date was taken from the server's local clock (`date.today()`), so "is this reaction
  still pending" depended on where the server runs.

## Decision
* **`NI_AUTH=demo`** (`identity/adapters/demo.py`): a request without the owner's key is the
  shared visitor (role `guest`): it reads every page and may ask the assistant, whose daily
  limit is then shared by all visitors (20 questions a day in total caps the AI cost). A
  request with `Authorization: Bearer <NI_ADMIN_TOKEN>` (24+ characters, compared in
  constant time) is the owner (admin). Start-up fails with a shorter key.
* Changing followed companies and testing alerts need a non-guest user (`member_user`);
  rounds and data loading stay admin-only. Visitors keep their stars in their own browser
  (localStorage), so they change nothing for anyone else; `GET /v1/me` tells the website
  what to show (no "Update now" for visitors).
* Responses are gzip-compressed; the snapshot is kept in memory until a round replaces it,
  and `/v1/companies` serves JSON made once per snapshot.
* Dates for "pending" use UTC.

## Consequences
* One instance only: the server runs the rounds itself and the database is one SQLite
  file. Two instances would run every round twice. Several instances need the scheduled
  round as its own job and Postgres (docs/05).
* No per-visitor rate limit in the app: put the demo behind the host's limits (or a CDN).
  Cost is still capped by the monthly LLM budget, the per-round call cap and the shared
  daily question limit.
* Before showing it publicly, check the terms of the news feeds we show headlines from
  (Yahoo Finance: personal and research use) — showing links and headlines in a free demo
  is a different use from a paid product.
