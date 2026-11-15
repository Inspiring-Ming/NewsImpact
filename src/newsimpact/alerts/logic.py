"""Which changes between two snapshots deserve an alert. Pure functions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from newsimpact.alerts.models import Alert, EventSnapshot


def _move(e: EventSnapshot) -> str:
    if e.stock_move is None:
        return "Stock reaction not measured yet."
    side = "worse" if e.stock_move < 0 else "better"
    return f"The stock did {abs(e.stock_move) * 100:.1f}% {side} than the {e.index_name}."


def _brief(e: EventSnapshot, fallback: str) -> str:
    body = "\n".join(f"• {line}" for line in e.brief) if e.brief else fallback
    return f"{body}\nNext: {e.next_step}" if e.next_step else body


def changes(
    previous: Mapping[str, EventSnapshot], current: Iterable[EventSnapshot], followed: set[str]
) -> list[Alert]:
    """Alerts for followed companies, most important change per event first."""
    out: list[Alert] = []
    for e in current:
        if e.ticker not in followed:
            continue
        before = previous.get(e.event_id)
        base = {"ticker": e.ticker, "article_url": e.article_url, "event_id": e.event_id}
        title = f"{e.company} · {e.event_type}"
        status = "Confirmed" if e.confirmed else "Not yet confirmed (one source)"
        if before is None:
            out.append(Alert(key=f"{e.event_id}|new", kind="new_event", title=f"New event: {title}",
                             text=_brief(e, f"{e.headline}\n{status}. {_move(e)}"),
                             **base))  # fmt: skip
            continue
        if e.confirmed and not before.confirmed:
            out.append(Alert(key=f"{e.event_id}|confirmed", kind="confirmed",
                             title=f"Now confirmed: {title}",
                             text=f"Another independent source, the company or a filing has "
                                  f"reported it.\n{e.headline}", **base))  # fmt: skip
        if e.unusual and e.stock_move is not None and before.stock_move is None:
            out.append(Alert(key=f"{e.event_id}|unusual", kind="unusual_move",
                             title=f"Unusual stock move: {title}",
                             text=f"{_move(e)} A move this large happens on fewer than 1 normal "
                                  f"day in 20.", **base))  # fmt: skip
        if e.updates > before.updates:
            text = f"{e.latest_update}: {e.headline}\n{status}."
            out.append(Alert(key=f"{e.event_id}|update{e.updates}", kind="new_update",
                             title=f"New update: {title}", text=text, **base))  # fmt: skip
    return out
