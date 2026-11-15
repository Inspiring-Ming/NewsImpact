"""Export JSON Schemas for every event into /schemas/events.

Each module's models.py is the source of truth and lists the events it
publishes in PUBLISHES; these files are the language-neutral copy for
non-Python services and client integrations. Modules are found automatically,
so a new module's events are exported without editing this script. CI fails if
the files drift (`make contracts-check`). The HTTP API's schema is served live
at /openapi.json.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path

import newsimpact
from newsimpact.shared.events import EventEnvelope

NOT_MODULES = {"app", "shared"}  # composition and toolkit, not business modules
OUT = Path(__file__).resolve().parents[1] / "schemas" / "events"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.schema.json"):
        old.unlink()
    schemas = {"envelope": EventEnvelope.model_json_schema()}
    for info in pkgutil.iter_modules(newsimpact.__path__):
        if not info.ispkg or info.name in NOT_MODULES:
            continue
        models = importlib.import_module(f"newsimpact.{info.name}.models")
        schemas.update(
            {e.EVENT_TYPE: e.model_json_schema() for e in getattr(models, "PUBLISHES", ())}
        )
    for name, schema in schemas.items():
        text = json.dumps(schema, indent=2, sort_keys=True) + "\n"
        (OUT / f"{name}.schema.json").write_text(text)
    print(f"wrote {len(schemas)} schemas to {OUT}")


if __name__ == "__main__":
    main()
