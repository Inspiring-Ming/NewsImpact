"""Write the API's OpenAPI document to web/openapi.json.

The website generates its typed API client from this file (`npm run gen:api`),
so any API change that would break the website fails its type check in CI.
"""

from __future__ import annotations

import json
from pathlib import Path

from newsimpact.app.api import create_app
from newsimpact.app.config import Settings
from newsimpact.app.wiring import build_services

OUT = Path(__file__).resolve().parents[1] / "web" / "openapi.json"


def main() -> None:
    # Never touches local state: in-memory store, no LLM, no price vendor (ignores .env choices).
    settings = Settings(
        env="test", profile="demo", store="memory", llm_preset="off", market_data="none"
    )
    app = create_app(build_services(settings))
    OUT.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
