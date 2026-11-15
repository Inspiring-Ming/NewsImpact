# 0032 – Multi-user ready (local sign-in first), CI per kind of risk

* Status: accepted
* Date: 2026-11-16

## Context
The product will be used by more than one person (design partners), each with
their own followed companies and alerts. Registration needs a sign-in provider
(Amazon Cognito, on the owner's AWS account). Building the multi-user parts
first, with a free local sign-in, lets them be tested now and makes the move to
Cognito a configuration step.

## Decision
* New module **`identity`**: `User` (id, email, roles; "admin" may run updates,
  load demo data, test alert channels) and the `Authenticator` port.
  `local.py` = one built-in admin, no sign-in (`NI_AUTH=local`, the default).
  Safe only where others cannot reach the site.
* **Per-user data**: followed companies and sent alerts are stored per user;
  alerts go to each user's channels (`Channels` port; `SharedChannels` = the
  configured Discord for everyone until users set their own).
* **API**: every `/v1` route needs a signed-in user (bearer token checked by the
  Authenticator); updates and demo loading need an admin; `/health` stays open.
* **Cognito next**: `identity/adapters/cognito.py` + one `AUTH` entry, after the
  owner approves the AWS setup and cost (free for the first 10,000 monthly
  active users, then about $0.015 per user per month; confirm on the AWS
  pricing page before setup).
* **CI**: five parallel jobs, one per kind of risk (python, web, docker,
  secrets, terraform); superseded runs are cancelled; every job has a time
  limit; the docker job starts the image and checks `/health`, the API and the
  website before scanning it; Dependabot also covers the website's npm
  packages and groups minor and patch updates.

## Consequences
+ Many users need one adapter and a setting, no rework.
- Until Cognito, the site must not be exposed to others (anyone reaching it is
  the admin).
