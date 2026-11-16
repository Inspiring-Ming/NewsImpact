"""MCP server: NewsImpact's read-only tools for AI assistants (Claude Desktop, Claude Code...).

    uv run --extra mcp python -m newsimpact.app.mcp      (speaks MCP over stdin/stdout)

The tools are the assistant module's toolbox (find_company, list_events, get_event,
search_articles) over the latest snapshot and the stored articles - exactly what the
website's "Ask NewsImpact" may see, defined once. The assistant you connect does the
thinking (and pays for it); this server only answers lookups, so it costs us nothing.

Local only for now: it runs as a process on this computer, reading the same database as
the website (NI_DB_PATH). Offering it to others (over HTTP) needs sign-in first (Cognito).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from newsimpact.app.views.news_data import SnapshotNewsData
from newsimpact.assistant.logic import Notebook, toolbox
from newsimpact.llm.models import ToolSpec

if TYPE_CHECKING:
    from newsimpact.app.wiring import Services

INSTRUCTIONS = (
    "NewsImpact detects market-moving events about large US and Australian companies in the "
    "news, checks how well each is sourced, and measures the stock move against its index. "
    "Use find_company, then list_events or search_articles, then get_event for details and "
    "article links. Facts only, not investment advice."
)


def build_server(svc: Services) -> Server[Any]:
    data = SnapshotNewsData(svc)

    def tools() -> dict[str, ToolSpec]:
        return {t.name: t for t in toolbox(data, Notebook())}

    async def list_tools(
        ctx: Any, params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(tools=[
            types.Tool(name=t.name, description=t.description, input_schema=t.input_schema)
            for t in tools().values()
        ])  # fmt: skip

    async def call_tool(ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
        spec = tools().get(params.name)
        if spec is None:
            return _result(f"unknown tool {params.name!r}", error=True)
        try:  # the stores are synchronous: run off the event loop
            text = await anyio.to_thread.run_sync(lambda: spec.run(**(params.arguments or {})))
        except (TypeError, ValueError) as exc:  # wrong or missing arguments
            return _result(f"bad arguments for {params.name}: {exc}", error=True)
        return _result(text)

    return Server("newsimpact", title="NewsImpact", instructions=INSTRUCTIONS,
                  on_list_tools=list_tools, on_call_tool=call_tool)  # fmt: skip


def _result(text: str, *, error: bool = False) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)],
                                is_error=error)  # fmt: skip


async def _serve() -> None:
    from newsimpact.app.wiring import build_services  # imported only when serving

    async with stdio_server() as (read, write):  # from here, stray prints go to stderr
        server = build_server(build_services())
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    anyio.run(_serve)


if __name__ == "__main__":
    main()
