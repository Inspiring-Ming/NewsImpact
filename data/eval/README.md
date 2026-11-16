# Evaluation data

`semantics_gold.jsonl` holds hand-labelled sentences about **fictional** companies.
`GET /v1/evaluation` (with the server running: `curl localhost:8000/v1/evaluation`) runs the configured analysis chain on them and reports
accuracy, macro-F1 and per-label precision/recall. Any change to the taxonomy, a
new step or an LLM must be compared here before it is used in the product.

Labels: `event_type` (taxonomy name or `other`), `is_speculative`, `attribution_kind`,
`cited_outlets` (taxonomy outlet ids), `is_background`. `note` explains hard cases
(paraphrases, history, traps). Rules: one label per field; label what the sentence
*reports as new*, not what it mentions. Add real-world-style examples, never copied
article text.
