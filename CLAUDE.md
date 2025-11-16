# CLAUDE.md - AI Assistant Guide for Codex Azazel

This document provides comprehensive guidance for AI assistants working with the Codex Azazel (BCE - Biblical Character Engine) codebase.

## Project Overview

**Codex Azazel** is a contradiction-aware Biblical character and event engine focused on New Testament data. The acronym BCE stands for "Biblical Character Engine" (with a possible future expansion to "Before Canon Engine" for pre-canonical texts).

### Core Purpose

- Provide structured, JSON-backed data for New Testament characters and events
- Enable per-source comparison (Mark, Matthew, Luke, John, Paul, Acts, etc.)
- Surface contradictions and conflicts between different source accounts
- Offer clean exports (JSON, Markdown) and CLI tools for data inspection
- Maintain a pure, simple API that is AI-friendly and human-readable

### Non-Goals

This project explicitly does NOT include:
- Frontend/UI or web application
- Debate engine or apologetics logic
- General-purpose Bible study app features
- LLM prompt logic or AI pipelines

It is a **data and analysis engine** designed to be consumed by other tools.

## Repository Structure

```
codex-azazel/
├── bce/                          # Main package
│   ├── __init__.py              # Package exports
│   ├── models.py                # Core dataclasses (Character, Event, etc.)
│   ├── storage.py               # JSON loading/saving with configurable data root
│   ├── queries.py               # High-level query API with LRU caching
│   ├── contradictions.py        # Comparison and conflict detection
│   ├── dossiers.py              # Build structured dossiers for export
│   ├── export.py                # Main export module (imports json/markdown)
│   ├── export_json.py           # JSON export helpers
│   ├── export_markdown.py       # Markdown export helpers
│   ├── validation.py            # Data validation helpers
│   ├── cli.py                   # Main CLI entry point
│   └── data/
│       ├── characters/          # Character JSON files
│       │   ├── jesus.json
│       │   ├── paul.json
│       │   ├── peter.json
│       │   ├── judas.json
│       │   └── pilate.json
│       └── events/              # Event JSON files
│           ├── crucifixion.json
│           ├── damascus_road.json
│           ├── betrayal.json
│           ├── resurrection_appearance.json
│           └── trial_before_pilate.json
├── tests/                       # Test suite
│   ├── test_basic.py
│   ├── test_cli.py
│   ├── test_contradictions.py
│   ├── test_dossiers.py
│   ├── test_dossier_markdown.py
│   ├── test_export.py
│   ├── test_storage.py
│   └── test_validation.py
├── examples/                    # Usage examples
│   ├── basic_usage.py
│   └── print_dossier_markdown.py
├── docs/
│   └── ROADMAP.md              # Project roadmap and phases
├── dev_cli.py                  # Development CLI (legacy, being phased out)
├── pyproject.toml              # Package configuration
├── README.md                   # User-facing documentation
└── .gitignore                  # Git ignore rules
```

## Core Data Models

### Character

Defined in `bce/models.py:15-20`:

```python
@dataclass(slots=True)
class Character:
    id: str                                  # Unique identifier (e.g., "jesus")
    canonical_name: str                      # Display name (e.g., "Jesus of Nazareth")
    aliases: List[str]                       # Alternative names
    roles: List[str]                         # e.g., ["teacher", "prophet", "messiah"]
    source_profiles: List[SourceProfile]     # Per-source data
```

### SourceProfile

Defined in `bce/models.py:8-11`:

```python
@dataclass(slots=True)
class SourceProfile:
    source_id: str                  # e.g., "mark", "matthew", "paul_undisputed"
    traits: Dict[str, str]          # Narrative/theological features
    references: List[str]           # Scripture references
```

### Event

Defined in `bce/models.py:32-36`:

```python
@dataclass(slots=True)
class Event:
    id: str                         # Unique identifier (e.g., "crucifixion")
    label: str                      # Display name
    participants: List[str]         # Character IDs involved
    accounts: List[EventAccount]    # Per-source accounts
```

### EventAccount

Defined in `bce/models.py:24-28`:

```python
@dataclass(slots=True)
class EventAccount:
    source_id: str           # Source identifier
    reference: str           # Scripture reference
    summary: str             # Account summary
    notes: Optional[str]     # Optional notes
```

## Module Responsibilities

### `bce/models.py`

Pure dataclass definitions with no business logic. Uses `slots=True` for efficiency.

### `bce/storage.py`

- JSON file I/O for characters and events
- Configurable data root via `configure_data_root(path)`
- List/load/save operations for characters and events
- Automatic query cache clearing on data changes
- Default data root: `bce/data/`

Key functions:
- `load_character(char_id: str) -> Character`
- `load_event(event_id: str) -> Event`
- `save_character(character: Character) -> None`
- `save_event(event: Event) -> None`
- `list_character_ids() -> List[str]`
- `list_event_ids() -> List[str]`
- `iter_characters() -> Iterator[Character]`
- `iter_events() -> Iterator[Event]`

### `bce/queries.py`

High-level query API with `@lru_cache` decorators for performance.

Key functions:
- `get_character(char_id: str) -> Character` (cached)
- `get_event(event_id: str) -> Event` (cached)
- `list_all_characters() -> List[Character]`
- `get_source_profile(char: Character, source_id: str) -> Optional[SourceProfile]`
- `list_events_for_character(char_id: str) -> List[Event]`
- `clear_cache() -> None` (clears LRU caches)

### `bce/contradictions.py`

Comparison and conflict detection between sources.

Key functions:
- `compare_character_sources(char_id: str) -> Dict[str, Dict[str, str]]`
  - Returns `trait -> source_id -> value` mapping
- `find_trait_conflicts(char_id: str) -> Dict[str, Dict[str, str]]`
  - Returns only traits that differ between sources
- `find_events_with_conflicting_accounts(event_id: str) -> Dict[str, Dict[str, str]]`
  - Returns event fields that differ between accounts

### `bce/dossiers.py`

Builds comprehensive JSON dossiers for characters and events.

Key functions:
- `build_character_dossier(char_id: str) -> dict`
  - Includes identity, traits by source, references, comparisons, conflicts
- `build_event_dossier(event_id: str) -> dict`
  - Includes identity, participants, accounts, conflicts
- `build_all_character_dossiers() -> list[dict]`
- `build_all_event_dossiers() -> list[dict]`

### `bce/export_json.py`

JSON export utilities for aggregating all characters or events.

### `bce/export_markdown.py`

Markdown export utilities for dossiers.

Key functions:
- `dossier_to_markdown(dossier: dict) -> str`
- `dossiers_to_markdown(dossiers: list[dict]) -> str`

### `bce/validation.py`

Data integrity validation.

Key function:
- `validate_all() -> List[str]`
  - Returns list of error messages (empty list = all checks passed)
  - Checks for duplicate IDs, loading failures, ID mismatches

### `bce/cli.py`

Main CLI entry point (registered as `bce` command in pyproject.toml).

Usage:
```bash
bce character <id> --format markdown
bce event <id> --format markdown
```

## Development Workflows

### Installation

```bash
# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run specific test file
pytest tests/test_contradictions.py

# Run with verbose output
pytest -v
```

### Testing Conventions

- All test files in `tests/` directory
- Test files named `test_*.py`
- Uses pytest framework
- Tests cover:
  - Basic loading and queries
  - CLI functionality with exit codes
  - Contradiction detection
  - Dossier building
  - Export functionality
  - Validation logic
  - Markdown generation

### Code Style

- Python 3.11+ required
- Type hints using `from __future__ import annotations`
- Dataclasses with `slots=True` for models
- `Dict`, `List`, `Optional` from typing module
- Lowercase with underscores for functions/variables
- Classes use PascalCase
- Private/internal functions prefixed with `_`

### JSON Data Conventions

**Character JSON Structure:**
```json
{
  "id": "character_id",
  "canonical_name": "Display Name",
  "aliases": ["Alternative", "Names"],
  "roles": ["role1", "role2"],
  "source_profiles": [
    {
      "source_id": "source_name",
      "traits": {
        "trait_key": "trait_value"
      },
      "references": ["Scripture 1:1", "Scripture 2:2"]
    }
  ]
}
```

**Event JSON Structure:**
```json
{
  "id": "event_id",
  "label": "Event Name",
  "participants": ["char_id1", "char_id2"],
  "accounts": [
    {
      "source_id": "source_name",
      "reference": "Scripture 1:1-10",
      "summary": "Event description",
      "notes": "Optional notes"
    }
  ]
}
```

### Common Source IDs

- `mark` - Gospel of Mark
- `matthew` - Gospel of Matthew
- `luke` - Gospel of Luke
- `john` - Gospel of John
- `paul_undisputed` - Undisputed Pauline epistles
- `acts` - Acts of the Apostles

## CLI Tools

### Main CLI (`bce`)

Installed entry point after `pip install -e .`:

```bash
# View character dossier as Markdown
bce character jesus --format markdown

# View event dossier as Markdown
bce event crucifixion --format markdown
```

Returns non-zero exit code if ID not found.

### Development CLI (`dev_cli.py`)

Legacy CLI, still functional:

```bash
# List all characters
python dev_cli.py list-chars

# Show character JSON
python dev_cli.py show-char jesus

# Show character dossier
python dev_cli.py show-char-dossier jesus

# List all events
python dev_cli.py list-events

# Show event JSON
python dev_cli.py show-event crucifixion

# Show event dossier
python dev_cli.py show-event-dossier crucifixion

# Export all characters to JSON
python dev_cli.py export-chars exports/all_characters.json

# Export all events to JSON
python dev_cli.py export-events exports/all_events.json
```

## Key Patterns for AI Assistants

### 1. When Adding New Characters

1. Create JSON file in `bce/data/characters/<char_id>.json`
2. Follow the character JSON schema exactly
3. Include at least one source_profile
4. Ensure `id` field matches filename (without .json)
5. Run validation: `python -c "from bce.validation import validate_all; print(validate_all())"`
6. Add tests if introducing new patterns

### 2. When Adding New Events

1. Create JSON file in `bce/data/events/<event_id>.json`
2. Follow the event JSON schema
3. Ensure participant IDs reference existing characters
4. Ensure `id` field matches filename
5. Run validation to check integrity

### 3. When Modifying Data Models

1. Update `bce/models.py` dataclasses
2. Update JSON loading in `bce/storage.py`
3. Update any dossier builders in `bce/dossiers.py`
4. Update tests to match new structure
5. Consider backward compatibility with existing JSON files

### 4. When Adding New Query Functions

1. Add to `bce/queries.py` if general-purpose
2. Use `@lru_cache` for expensive lookups
3. Return immutable types when possible
4. Document return types clearly
5. Add corresponding tests

### 5. When Working with Contradictions

Use the contradiction helpers to surface differences:

```python
from bce import contradictions

# Get all traits mapped by source
comparison = contradictions.compare_character_sources("jesus")

# Get only conflicting traits
conflicts = contradictions.find_trait_conflicts("jesus")

# Get conflicting event accounts
event_conflicts = contradictions.find_events_with_conflicting_accounts("crucifixion")
```

### 6. Cache Management

The query module uses `@lru_cache` for performance. When data changes:
- `storage.save_character()` automatically clears cache
- `storage.save_event()` automatically clears cache
- `storage.configure_data_root()` automatically clears cache
- Manually call `queries.clear_cache()` if needed

### 7. Testing Data Changes

Always run the validation suite after data changes:

```python
from bce.validation import validate_all

errors = validate_all()
if errors:
    for error in errors:
        print(f"ERROR: {error}")
else:
    print("All validation checks passed!")
```

### 8. Export Workflows

To generate exports for external tools:

```python
from bce.export import export_all_characters, export_all_events

# Export to JSON
export_all_characters("output/characters.json")
export_all_events("output/events.json")

# Generate Markdown dossiers
from bce.dossiers import build_character_dossier
from bce.export import dossier_to_markdown

dossier = build_character_dossier("jesus")
markdown = dossier_to_markdown(dossier)
print(markdown)
```

## File References in Code

When discussing code locations, use this format:
- `bce/models.py:15-20` for Character dataclass
- `bce/storage.py:64-69` for load_character function
- `bce/queries.py:12-14` for get_character function

## Roadmap Awareness

Currently in **Phase 0** (Core, Dossiers, Export & Examples) - COMPLETE

Next phases:
- **Phase 1**: Data Coverage & Validation (v0 canon, more characters/events)
- **Phase 2**: Thematic Tagging & Query Helpers
- **Phase 3**: Conflict Objects & Ergonomics
- **Phase 4**: Stable API Surface for External Tools
- **Phase 5**: Optional Extensions (HTTP API, additional formats)

See `docs/ROADMAP.md` for complete phase details.

## Common Pitfalls to Avoid

1. **Don't bypass the query API**: Use `queries.get_character()` instead of `storage.load_character()` to benefit from caching
2. **Don't forget to clear cache**: If manually modifying JSON files, call `queries.clear_cache()`
3. **Don't create circular dependencies**: Keep imports clean (models → storage → queries → contradictions/dossiers)
4. **Don't add UI code**: This is a data engine, not a frontend
5. **Don't hardcode data root paths**: Use `storage.configure_data_root()` for custom data locations
6. **Don't skip validation**: Always run `validate_all()` after data changes

## Testing Strategy

Tests should:
- Use pytest fixtures for reusable test data
- Test both success and failure cases
- Verify CLI exit codes (0 for success, 1+ for errors)
- Check that validation catches malformed data
- Verify exports produce expected structure
- Test contradiction detection with known conflicts

## Git Workflow

- Main development happens on feature branches
- Branch naming: `claude/claude-md-<session-id>`
- Commit messages should be clear and descriptive
- Push to feature branch: `git push -u origin <branch-name>`
- No force pushes to main/master without explicit permission

## Package Information

- **Name**: codex-azazel
- **Version**: 0.1.0
- **Python Requirement**: >= 3.11
- **Build System**: hatchling
- **License**: MIT
- **Dev Dependencies**: pytest
- **CLI Entry Point**: `bce` → `bce.cli:main`

## Quick Reference Commands

```bash
# Install package in dev mode
pip install -e .[dev]

# Run all tests
pytest

# Run tests with coverage
pytest --cov=bce

# List characters
python dev_cli.py list-chars

# View character as markdown
bce character jesus --format markdown

# Validate all data
python -c "from bce.validation import validate_all; print(validate_all() or 'OK')"

# Export everything
python dev_cli.py export-chars exports/characters.json
python dev_cli.py export-events exports/events.json
```

---

**Last Updated**: 2025-11-16
**Current Phase**: Phase 0 (Complete)
**Python Version**: 3.11+
