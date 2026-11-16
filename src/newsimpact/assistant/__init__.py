"""ASSISTANT - answer a person's question from our own data, and say where it comes from.

The model may only look things up through read-only tools over what NewsImpact
already holds (events, their sources and stock moves, stored articles); it never
browses the web. The same tools are offered to outside AI assistants over MCP
(app/mcp.py), so there is one definition of what an AI may see.

Every answer is checked before anyone sees it (shared/guardrails.py): no advice
words, and every number must appear in what the tools returned. Links are kept
only if a tool returned them. Each person has a daily question limit, and every
model step is priced and recorded against the monthly budget (llm module).
Publishes / consumes: nothing (called by the API: app/api/routes/assistant.py).
"""
