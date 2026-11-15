"""What every router may use: the services, the monitor and small per-process state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from newsimpact.app.monitor import BackgroundMonitor
from newsimpact.app.wiring import Services


@dataclass
class ApiContext:
    svc: Services
    monitor: BackgroundMonitor
    demo_loaded: bool = False
    cache: dict[str, Any] = field(default_factory=dict)  # results computed once per process
