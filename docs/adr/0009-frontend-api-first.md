# 0009 – API-first web frontend (React + TypeScript SPA, OIDC)

* Status: accepted (built in `web/`, see 0020) (implementation in Phase 4)
* Date: 2026-11-14

## Context
Clients will judge the product through a UI, while larger clients will also
integrate programmatically. We need both without duplicating logic, at near-
zero hosting cost, without vendor lock-in.

## Decision
* The web app is a static React + TypeScript (Vite) SPA in `frontend/`,
  hosted on S3 + CloudFront.
* It uses only the public versioned `/v1` API; its typed client is generated
  from `/openapi.json`, so API changes that break the UI fail CI.
* Authentication via OIDC (Amazon Cognito first); the API validates JWTs and
  takes `tenant_id` from claims.
* Push integrations (webhooks, later SSE/Slack/Teams) belong to a future
  `notifications` capability consuming events such as `StorylineUpdated`.
* Next.js/SSR only if we need SEO or server rendering (e.g. a public
  marketing site, which stays separate).

## Consequences
+ One integration surface; UI and customers always see the same capabilities.
+ Hosting cost ≈ $1/month; IdP and UI framework are replaceable.
− SPA needs care for auth token handling (use a vetted OIDC library, PKCE).
