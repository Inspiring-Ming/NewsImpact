from newsimpact.shared.bus import InMemoryEventBus
from newsimpact.shared.events import EventEnvelope


def test_failing_handler_is_isolated_and_dead_lettered() -> None:
    bus = InMemoryEventBus()
    received: list[str] = []

    def boom(_: EventEnvelope) -> None:
        raise RuntimeError("boom")

    bus.subscribe("t", boom)
    bus.subscribe("t", lambda e: received.append(e.id))
    bus.publish(EventEnvelope(source="/x", type="t", data={}))

    assert len(received) == 1
    assert len(bus.dead_letters) == 1
