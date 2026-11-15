"""LLM - one controlled gateway to language models, local or hosted.

Where LLMs are used (and only there):
  * semantics: the optional "llm" analysis step (event type, background,
    speculation, attribution) - see semantics/adapters/llm_classifier.py.
Everything else in the pipeline is deterministic and free.

How cost and change are controlled:
  * one setting, NI_LLM_PRESET: off (default) | quality (Claude Opus 5.5) |
    economy (Claude Haiku 5.5) | local (Ollama, $0) - each preset and its reason
    is in data/reference/llm_models.json
  * every call: cache by content hash -> budget check -> call -> record spend
  * monthly budget (NI_LLM_MONTHLY_BUDGET_USD) and per-round call cap; when
    either is reached, callers keep the free baseline result
  * prices live in the same file (dated, with source)
  * any new provider = one adapter implementing LlmProvider

Publishes / consumes: nothing (called through the TextModel port of semantics, and by the
event briefs in app/views/briefs.py).
"""
