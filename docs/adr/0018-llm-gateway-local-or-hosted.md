# 0018 – One LLM gateway: local or hosted, budgeted, cached, evaluated

* Status: accepted (refines 0005; presets in llm_models.json, website instead of CLI: 0020)
* Date: 2026-11-15

## Context
LLMs could improve classification (paraphrases, implicit attribution), but
costs can run away, providers change, and quality has to be shown rather
than assumed.

## Decision
* LLMs are used in exactly one place for now: an optional semantics step,
  `llm_classifier`. It may answer only with taxonomy labels, enforced by
  JSON-schema enums.
* All calls go through `llm.LlmGateway`, in this order:
  1. a response cache keyed by content hash;
  2. a per-round call cap and a monthly budget, checked against the
     worst-case cost *before* the call;
  3. the call itself;
  4. a spend ledger entry.
  Prices come from the dated `llm_prices.json`; an unknown paid model is
  priced at the most expensive known rate.
* Providers are adapters:
  * Ollama for local models ($0, data stays on the machine);
  * Anthropic through the official SDK, with structured outputs, prompt
    caching on the fixed instructions, low effort and server-side refusal
    fallback. The SDK is an optional extra.
* "candidates" scope (default): only claims where the free baseline saw
  something are sent to the model.
* Every failure path keeps the free baseline result.
* Model choice is made with `newsimpact evaluate --live` on the labelled set,
  which reports quality and spend together.

## Consequences
+ Switching between local, cheap hosted and strong hosted models is a setting.
+ The worst-case monthly cost is bounded by configuration.
− Quality of a given local model is unknown until evaluated; no provider was
  called during development (all adapter tests use fakes).
