# 0012 – One file template for every module; data lives with its module

* Status: accepted (amends 0008)
* Date: 2026-11-14

## Context
After 0008, the code was grouped by business module, but readers still had
to jump around:
* each module's data types lived in a separate central `contracts/` folder;
* modules had different extra files (`scoring.py`, `playbook.py`,
  `event_study.py`, `follow_up.py`);
* adapter files were named inconsistently (`entity_file.py`,
  `relationships_file.py`, `playbook_file.py`);
* names mixed jargon (`kernel`, `container`, `ingestion`) with business terms.

## Decision
* Every module has the same files: `__init__.py` (module card), `models.py`,
  `logic.py` (only where there is real math), `ports.py`, `service.py`, and
  `adapters/`.
* A module's data and events live in **its own `models.py`**, which lists its
  events in `PUBLISHES`. The `contracts/` folder is removed.
* Other modules may import a module's `models.py` and nothing else. This is
  enforced by an import-linter independence contract that ignores only
  `* -> *.models` imports.
* Adapter files are named after their technology: `json_file.py`, `memory.py`,
  `rss.py`, `gdelt.py`, `lexicon.py`, `synthetic.py`.
* Plain names: `shared/` (was `kernel/`), `app/wiring.py` (was
  `container.py`), `sources` (was `ingestion`), and service classes named
  `<Module>Service`.
* There are four architecture rules instead of five (docs/03-architecture.md).

## Consequences
+ To understand a module, open one folder and read `__init__.py`,
  `models.py`, `service.py`, in that order.
+ Every module looks the same, so new code has an obvious home.
− Modules now depend on each other's `models.py` directly rather than on a
  neutral contracts package. Rule 3 (models import only `shared` and other
  models) keeps that coupling to data. The JSON Schemas in `schemas/events/`
  remain the neutral copy for non-Python consumers.
