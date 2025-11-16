# Codex Azazel: BCE (Biblical Character Engine)

## Overview

Codex Azazel's BCE (Biblical Character Engine) is a small Python library for modeling New Testament characters and events as structured data, currently focused on biblical characters; "Before Canon Engine" is a possible future specialization for broader pre-canonical corpora. It represents per-source profiles (Mark, Matthew, Luke, John, undisputed Paul, Acts, etc.) so that you can compare portrayals, trace contradictions, and support historical-critical analysis.

All core data lives in JSON (`bce/data/characters`, `bce/data/events`), and the Python API is designed to be simple, pure, and AI-friendly.

## Features

- **Dataclasses for characters and events**
  - `Character` objects with per-source `SourceProfile`s.
  - `Event` objects with per-source `EventAccount`s.
- **JSON-backed storage**
  - Characters in `bce/data/characters/*.json`.
  - Events in `bce/data/events/*.json`.
- **Query API**
  - Load a character or event by ID.
  - List all character IDs and event IDs.
  - List events in which a given character appears.
- **Contradiction helpers**
  - Compare character traits across sources.
  - Find traits and event fields where sources differ.
- **Export helpers**
  - Dump all characters or all events to aggregated JSON files for frontends or external tools.
- **CLI for quick inspection**
  - List characters and events, show details, and run exports from the command line.
- **Examples for onboarding**
  - `examples/basic_usage.py` demonstrates the main APIs in a single script.

## Project layout

A simplified view of the repository:

```text
codex-azazel/
  pyproject.toml
  README.md
  cli.py
  examples/
    basic_usage.py
  bce/
    __init__.py
    models.py          # Character, SourceProfile, Event, EventAccount dataclasses
    storage.py         # JSON-backed loading and saving of characters/events
    queries.py         # High-level query API (characters, events, listings)
    contradictions.py  # Comparison and conflict helpers
    export.py          # Aggregated JSON export helpers
    data/
      characters/
        jesus.json
        paul.json
        peter.json
        judas.json
        pilate.json
        ...
      events/
        crucifixion.json
        damascus_road.json
        betrayal.json
        trial_before_pilate.json
        resurrection_appearance.json
        ...
```

## Quickstart: CLI

From the repository root:

```bash
python cli.py list-chars
python cli.py show-char jesus
python cli.py list-events
python cli.py show-event crucifixion

python cli.py export-chars exports/all_characters.json
python cli.py export-events exports/all_events.json
```

These commands read from the JSON data under `bce/data` and print or export structured representations.

## Quickstart: Python

Basic usage from a Python shell or script:

```python
from bce import queries, contradictions

# Load a character
jesus = queries.get_character("jesus")
print(jesus.id, jesus.canonical_name)

# List IDs
print(queries.list_character_ids())
print(queries.list_event_ids())

# Compare traits for Jesus across sources
comparison = contradictions.compare_character_sources("jesus")
print(comparison)
```

For a more complete walkthrough, see `examples/basic_usage.py`.

## Development

From a checkout of the repo:

```bash
pip install -e .[dev]
pytest
```

This installs the package in editable mode with development dependencies (including the test runner) and runs the test suite.

After installation, you can also use the installed CLI entry point instead of calling the module directly:

```bash
bce character jesus --format markdown
bce event crucifixion --format markdown
```

## Dossiers & CLI

Codex Azazel can build structured dossiers for characters and events and export them as Markdown.

### Programmatic usage

```python
from bce.dossiers import build_character_dossier
from bce.export import dossier_to_markdown

dossier = build_character_dossier("jesus")
md = dossier_to_markdown(dossier)
print(md)
```

See `examples/print_dossier_markdown.py` for a runnable example.

### CLI usage

You can also inspect a single dossier from the command line:

```bash
# Character
python -m bce.cli character jesus --format markdown

# Event
python -m bce.cli event crucifixion --format markdown
```

If you pass an unknown ID, the CLI returns a non-zero exit code and prints an error message to stderr.

## Data model (brief)

BCE centers on a small set of JSON-backed dataclasses:

- **Character**
  - `id`, `canonical_name`, `aliases`, `roles`.
  - `source_profiles: list[SourceProfile]`, one profile per source (Mark, Matthew, Luke, John, Paul, Acts, etc.).
- **SourceProfile**
  - `source_id: str` (e.g. `"mark"`, `"matthew"`).
  - `traits: dict[str, str]` for narrative and theological features.
  - `references: list[str]` of scripture references.
- **Event**
  - `id`, `label`, `participants: list[str]` (character IDs).
  - `accounts: list[EventAccount]`, one account per source.
- **EventAccount**
  - `source_id: str`.
  - `reference: str` (scripture range).
  - `summary: str` and optional `notes: str | None`.

All of these map directly to JSON objects and are safe to edit by hand.

## Status and next steps

BCE is an early-stage engine focused on New Testament characters and a core set of events. Planned directions include:

- **More coverage**
  - Additional characters, events, and per-source traits.
- **Richer trait vocabulary**
  - More structured keys for Christology, narrative roles, and event features.
- **Integration layers**
  - Optional read-only HTTP API (e.g. FastAPI/Flask) over the existing query and export functions.
  - Lightweight frontend or visualization tools built on aggregated JSON exports.

The core design goal is to keep the data model and API small, explicit, and friendly to both human readers and AI tools.
