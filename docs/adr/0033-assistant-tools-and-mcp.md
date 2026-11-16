# 0033 – AI assistant: read-only tools over our data, on the website and over MCP

* Status: accepted
* Date: 2026-11-16

## Context
Investors want to ask about an event in their own words ("why did Atlassian
fall?", "who confirmed the Nvidia CEO change?"). AI assistants (Claude Desktop,
Claude Code and other agents) increasingly use products through tools, with
the Model Context Protocol (MCP) as the common standard. The answer must stay
as trustworthy as the rest of the product: facts from our data, its sources,
no advice, no invented numbers, and a known cost.

## Decision
* New module **`assistant`**. `logic.py` defines four **read-only tools**
  (find_company, list_events, get_event, search_articles) over the `NewsData`
  port, and the instructions. Every tool result is written to a **Notebook**:
  the only ground an answer may use.
* **Checks before anyone sees an answer** (`shared/guardrails.py`, shared with
  the briefs): no advice words, every number present in the Notebook (or the
  question); links kept only if a tool returned them. Failing answers are not
  shown. "Not in our data" is a normal answer.
* **Tool use runs through the llm gateway** (`run_tools`): a budget check
  before starting (worst case: every step at full length), and every step's
  cost recorded in the same ledger as the classifier and briefs. The Anthropic
  adapter uses the SDK's **tool runner** (`client.beta.messages.tool_runner`),
  capped at `max_steps`; other providers can implement `run_tools` later.
* **Data**: `app/views/news_data.py` reads the latest snapshot and the stored
  articles, formatted as on the website. Nothing hand-written.
* **Two entry points, one toolbox**: `POST /v1/assistant/ask` (website "Ask"
  tab on the event page; signed-in users; per-person daily limit) and
  **`app/mcp.py`**, an MCP server (official `mcp` SDK, low-level server with
  explicit schemas) over stdio (`make mcp`). The connected assistant does the
  thinking and pays for it.
* Limits and their reasons: `methodology.json` "assistant" (20 questions per
  person per day, 6 model steps, 1,024 tokens per step).

## Not chosen (for now)
* An agent running the hourly round: it is a fixed sequence of steps; an agent
  would add cost and unpredictability, with nothing to gain.
* Vector search (embeddings): a few thousand articles are searched well by
  words; with Postgres it becomes full-text search and, if needed, pgvector.
* Managed Agents: suited to long or scheduled work (e.g. a weekly research note
  per watchlist); revisit after this is in use.
* Frameworks such as LangChain: an extra layer over the official SDKs that
  changes often; the Anthropic SDK and MCP are the standards.
* MCP over HTTP for other people: needs sign-in (Cognito) first.

## Consequences
* Measured on real data (2026-11-16, economy preset = Claude Haiku 5.5): five
  questions, US$0.0056 in total; answers cited the right articles, a question
  with no data in our store got "Not in our data", and an advice question was
  held back by the checks.
* A new lookup for AIs = one entry in `toolbox` and its data in `NewsData`;
  the website and MCP get it at once.
