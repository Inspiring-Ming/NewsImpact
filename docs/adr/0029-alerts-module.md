# 0029 – Alerts for followed companies (Discord first)

* Status: accepted
* Date: 2026-11-16

## Context
Professional users need to hear when something changes for the companies they
follow, without keeping the site open (ADR 0028). The followed list lived in
the browser, so the server could not know whom to alert.

## Decision
* New module `alerts` (same template as the others): after each monitor round
  the app passes a snapshot of every event; `alerts.logic.changes` compares it
  with the previous snapshot and produces an alert, for followed companies
  only, when: a new event appears, an event becomes confirmed, an unusual
  stock move is measured, or a new update arrives. The first round only
  records a baseline; each alert has a key and is never sent twice.
* **Discord first:** an incoming webhook is free and needs no account system.
  The webhook URL is a secret (anyone holding it can post to the channel): it
  lives only in the git-ignored `.env` (`NI_DISCORD_WEBHOOK_URL`), is never
  logged, and errors are re-raised without it. Unset = alerts are worked out
  but not sent. Email through AWS SES is the scalable next channel: another
  `Notifier` adapter, no change to the logic.
* **Followed companies moved to the server** (`/v1/watchlist`), one list for
  now (a single user). Before the site is deployed for others, the list and
  these endpoints need accounts and login.

## Consequences
+ Alerts arrive on the phone through Discord.
- No login yet: the follow endpoints are only safe on a local or private server.
