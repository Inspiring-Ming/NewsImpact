"""SEMANTICS - what an article claims, about whom, and what kind of event it is.

Analysis is a chain: an extractor finds claims (sentences naming a known
company), then each step adds one kind of analysis: event type and aspect
(from data/reference/taxonomy.json), sentiment, speculation, extra signals.

Extend it:
  * New event type, aspect or word list -> edit taxonomy.json (no code).
  * New measurement -> add a ClaimStep adapter, list it in NI_SEMANTIC_STEPS.
  * New technique (LLM) -> an adapter implementing ClaimExtractor/ClaimStep.

Publishes: ClaimsExtracted
Consumes:  ArticleIngested
"""
