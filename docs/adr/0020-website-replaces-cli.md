# 0020 – An interactive website replaces the command line

* Status: accepted (implements 0009; supersedes the CLI parts of 0015-0019)
* Date: 2026-11-15

## Context
The product is shown to clients and used by analysts, not developers. A
command line made results hard to read: storylines, evidence tables and price
reactions are visual by nature.

## Decision
* The website lives in `web/` (React + TypeScript + Vite) and talks only to
  the versioned `/v1` API. Its typed client is generated from the server's
  OpenAPI document, which is committed. `make contracts-check` fails CI on
  drift.
* The API serves the built site at `/`, so one container is the whole
  product. The same files can later move to S3 + CloudFront (ADR 0009).
* Monitoring runs inside the server:
  * on a timer (`NI_MONITOR_EVERY_MINUTES`);
  * or on demand from the website ("Run a monitoring round now");
  * on AWS, EventBridge calls the same `run_round()`.
* Everything the CLI did is now an API endpoint and a page: overview,
  storylines (with price chart and evidence), outlets and coverage,
  calibration, quality evaluation, and method (every setting with its reason).
* The CLI and its text reports were deleted.

## Consequences
+ One clear interface for clients and analysts; integrations use the same API.
+ No duplicated presentation logic: the API returns data, the website renders it.
− A Node toolchain joins the build (Node 22, pinned dependencies,
  `package-lock.json`).
