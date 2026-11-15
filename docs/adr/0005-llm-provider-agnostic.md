# 0005 – LLM access through a provider-agnostic port

* Status: accepted
* Date: 2026-11-14

## Context
LLM vendors, models and prices change quickly. News text is untrusted
input (prompt-injection risk).

## Decision
Business modules depend on `ClaimExtractor` / `ClaimStep` (ADR 0013); LLM-based analyzers depend on the
`LLMClient` port. Provider adapters (Anthropic API, Bedrock, others) are
chosen by configuration. Rules: cheap deterministic filter first; cache by
content hash; structured (JSON-schema-validated) outputs; never let article
text trigger tools or actions; record `model_version` with every output;
evaluate every new model against a labelled set before switching.

## Consequences
+ Switch or A/B models without touching business logic; cost is controllable.
− Need to maintain an evaluation dataset (which is also a product asset).
