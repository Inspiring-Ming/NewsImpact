"""Export JSON Schemas for every event into /schemas/events.

Each module's models.py is the source of truth and lists its events in
PUBLISHES; these files are the language-neutral copy for non-Python services
and client integrations. CI fails if they drift (`make schemas-check`). The
HTTP API's schema is served live at /openapi.json.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from newsimpact.shared.events import EventEnvelope

MODULES = (
    "sources",
    "semantics",
    "reliability",
    "storylines",
    "impact",
    "market",
    "validation",
    "llm",
)
OUT = Path(__file__).resolve().parents[1] / "schemas" / "events"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.schema.json"):
        old.unlink()
    schemas = {"envelope": EventEnvelope.model_json_schema()}
    for module in MODULES:
        models = importlib.import_module(f"newsimpact.{module}.models")
        schemas.update({e.EVENT_TYPE: e.model_json_schema() for e in models.PUBLISHES})
    for name, schema in schemas.items():
        text = json.dumps(schema, indent=2, sort_keys=True) + "\n"
        (OUT / f"{name}.schema.json").write_text(text)
    print(f"wrote {len(schemas)} schemas to {OUT}")


if __name__ == "__main__":
    main()
