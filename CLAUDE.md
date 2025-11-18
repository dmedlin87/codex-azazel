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
├── bce/                          # Main package (23 modules)
│   ├── __init__.py              # Package exports and public API
│   ├── api.py                   # HIGH-LEVEL API (recommended entry point)
│   ├── models.py                # Core dataclasses (Character, Event, SourceProfile, etc.)
│   ├── storage.py               # JSON loading/saving with configurable data root
│   ├── queries.py               # Query API with caching
│   ├── contradictions.py        # Comparison and conflict detection
│   ├── dossiers.py              # Build structured dossiers for export
│   ├── dossier_types.py         # TypedDict definitions for dossiers
│   ├── search.py                # Full-text search across characters and events
│   ├── export.py                # Main export facade
│   ├── export_json.py           # JSON export helpers
│   ├── export_markdown.py       # Markdown export helpers
│   ├── export_csv.py            # CSV export helpers
│   ├── export_citations.py      # Citation export (BibTeX, etc.)
│   ├── export_graph.py          # Graph/network export (GraphSnapshot)
│   ├── validation.py            # Data validation helpers
│   ├── config.py                # Configuration management (BceConfig)
│   ├── cache.py                 # Cache registry and invalidation
│   ├── exceptions.py            # Structured exception hierarchy
│   ├── sources.py               # Source metadata management
│   ├── services.py              # Service layer
│   ├── bibles.py                # Bible text integration
│   ├── cli.py                   # Main CLI entry point
│   └── data/
│       ├── characters/          # Character JSON files (62 total)
│       │   ├── jesus.json
│       │   ├── paul.json
│       │   ├── peter.json
│       │   ├── judas.json
│       │   ├── pilate.json
│       │   └── ... (57 more characters)
│       ├── events/              # Event JSON files (10 total)
│       │   ├── crucifixion.json
│       │   ├── damascus_road.json
│       │   ├── betrayal.json
│       │   ├── resurrection_appearance.json
│       │   ├── trial_before_pilate.json
│       │   └── ... (5 more events)
│       └── sources.json         # Source metadata
├── tests/                       # Test suite (24 files, 74 test functions)
│   ├── test_api.py              # API surface tests
│   ├── test_basic.py
│   ├── test_bibles.py           # Bible text integration tests
│   ├── test_cli.py
│   ├── test_contradictions.py
│   ├── test_data_integrity.py   # Data integrity tests
│   ├── test_dossiers.py
│   ├── test_dossier_markdown.py
│   ├── test_dossier_types.py
│   ├── test_error_handling.py   # Exception handling tests
│   ├── test_export.py
│   ├── test_export_citations.py
│   ├── test_export_csv.py
│   ├── test_export_graph.py
│   ├── test_export_json.py
│   ├── test_integration.py      # Integration tests
│   ├── test_main_cli.py
│   ├── test_models.py
│   ├── test_models_helpers.py
│   ├── test_queries.py
│   ├── test_search.py           # Search functionality tests
│   ├── test_storage.py
│   ├── test_tags.py             # Tag-based query tests
│   └── test_validation.py
├── examples/                    # Usage examples
│   ├── basic_usage.py
│   └── print_dossier_markdown.py
├── docs/
│   ├── ROADMAP.md              # Project roadmap and phases
│   ├── SCHEMA.md               # API schema documentation
│   ├── DATA_ENTRY_GUIDE.md     # Guide for adding data
│   └── features.md             # Feature documentation
├── dev_cli.py                  # Development CLI (legacy, still functional)
├── start.ps1                   # PowerShell startup script (Windows)
├── pyproject.toml              # Package configuration
├── README.md                   # User-facing documentation
├── CHANGELOG.md                # Version history
├── CLAUDE.md                   # This file - AI assistant guide
└── .gitignore                  # Git ignore rules
```

## Core Data Models

### Character

Defined in `bce/models.py:30-52`:

```python
@dataclass(slots=True)
class Character:
    id: str                                  # Unique identifier (e.g., "jesus")
    canonical_name: str                      # Display name (e.g., "Jesus of Nazareth")
    aliases: List[str]                       # Alternative names
    roles: List[str]                         # e.g., ["teacher", "prophet", "messiah"]
    source_profiles: List[SourceProfile]     # Per-source data
    relationships: List[dict]                # Character relationships (NEW in Phase 0.5)
    tags: List[str]                          # Topical tags (NEW in Phase 2)

    # Helper methods
    def get_source_profile(self, source_id: str) -> Optional[SourceProfile]
    def list_sources(self) -> List[str]
    def has_trait(self, trait: str, source: Optional[str] = None) -> bool
```

### SourceProfile

Defined in `bce/models.py:8-18`:

```python
@dataclass(slots=True)
class SourceProfile:
    source_id: str                  # e.g., "mark", "matthew", "paul_undisputed"
    traits: Dict[str, str]          # Narrative/theological features
    references: List[str]           # Scripture references

    # Helper methods
    def has_trait(self, trait: str) -> bool
    def get_trait(self, trait: str, default: Optional[str] = None) -> Optional[str]
```

### SourceMetadata

Defined in `bce/models.py:21-27` (NEW in Phase 0.5):

```python
@dataclass(slots=True)
class SourceMetadata:
    source_id: str                  # e.g., "mark", "matthew"
    date_range: Optional[str]       # e.g., "70-75 CE"
    provenance: Optional[str]       # e.g., "Rome" or "Antioch"
    audience: Optional[str]         # e.g., "Gentile Christians"
    depends_on: List[str]           # Sources this one likely depends on
```

### Event

Defined in `bce/models.py:83-90`:

```python
@dataclass(slots=True)
class Event:
    id: str                         # Unique identifier (e.g., "crucifixion")
    label: str                      # Display name
    participants: List[str]         # Character IDs involved
    accounts: List[EventAccount]    # Per-source accounts
    parallels: List[dict]           # Parallel pericope records (NEW in Phase 0.5)
    tags: List[str]                 # Topical tags (NEW in Phase 2)
```

### EventAccount

Defined in `bce/models.py:75-80`:

```python
@dataclass(slots=True)
class EventAccount:
    source_id: str           # Source identifier
    reference: str           # Scripture reference
    summary: str             # Account summary
    notes: Optional[str]     # Optional notes
```

## Module Responsibilities

### **RECOMMENDED ENTRY POINT: `bce/api.py`**

**The `bce.api` module is the recommended high-level entry point for external tools.** It provides a stable, ergonomic API surface that wraps lower-level modules.

Key functions:
- **Data access**: `get_character(id)`, `get_event(id)`, `list_character_ids()`, `list_event_ids()`
- **Dossiers**: `build_character_dossier(id)`, `build_event_dossier(id)`, `build_all_character_dossiers()`, `build_all_event_dossiers()`
- **Conflicts**: `summarize_character_conflicts(id)`, `summarize_event_conflicts(id)`
- **Search & Tags**: `search_all(query, scope)`, `list_characters_with_tag(tag)`, `list_events_with_tag(tag)`
- **Export**: `export_all_characters()`, `export_all_events()`, `export_characters_csv(path)`, `export_events_csv(path)`, `export_citations(format)`
- **Graph**: `build_graph_snapshot()` - Returns a `GraphSnapshot` with nodes and edges
- **Bible text**: `list_bible_translations()`, `get_verse_text(book, chapter, verse, translation)`, `get_parallel_verse_text(book, chapter, verse, translations)`

**Always prefer `bce.api` over direct module imports when building external tools.**

### `bce/models.py`

Pure dataclass definitions with helper methods. Uses `slots=True` for efficiency. Now includes:
- `Character` with helper methods: `get_source_profile()`, `list_sources()`, `has_trait()`
- `SourceProfile` with helper methods: `has_trait()`, `get_trait()`
- `Event` with new fields: `parallels`, `tags`
- `EventAccount` (unchanged)
- `SourceMetadata` (new in Phase 0.5) for source-level metadata

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
- `_find_conflicts(comparison: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]`
  - Internal helper function extracted in commit 60c183b to improve code reusability

### `bce/dossiers.py`

Builds comprehensive JSON dossiers for characters and events.

Key functions:
- `build_character_dossier(char_id: str) -> dict`
  - Includes identity, traits by source, references, comparisons, conflicts
- `build_event_dossier(event_id: str) -> dict`
  - Includes identity, participants, accounts, conflicts
- `build_all_character_dossiers() -> list[dict]`
- `build_all_event_dossiers() -> list[dict]`

### `bce/dossier_types.py`

Type definitions for dossier structures to improve type safety and code clarity.

Key types:
- `CharacterDossier` - TypedDict defining the structure of character dossiers
- `EventDossier` - TypedDict defining the structure of event dossiers
- `EventAccountDossier` - TypedDict for event account entries
- Constants: `DOSSIER_KEY_*` - String constants for dossier dictionary keys to avoid string literals throughout the codebase

This module was added in commit 60c183b (Nov 16, 2025) to extract type definitions and improve maintainability.

### `bce/export_json.py`

JSON export utilities for aggregating all characters or events.

### `bce/export_markdown.py`

Markdown export utilities for dossiers.

Key functions:
- `dossier_to_markdown(dossier: dict) -> str`
- `dossiers_to_markdown(dossiers: list[dict]) -> str`

### `bce/export_csv.py` (NEW in Phase 0.5)

CSV export utilities for tabular data exports.

Key functions:
- `export_characters_csv(output_path: str, include_fields: Optional[List[str]]) -> None`
- `export_events_csv(output_path: str, include_fields: Optional[List[str]]) -> None`

### `bce/export_citations.py` (NEW in Phase 0.5)

Citation export utilities for academic references.

Key functions:
- `export_citations(format: str = "bibtex") -> List[str]`
  - Exports citations for sources, characters, and events in BibTeX or other formats

### `bce/export_graph.py` (NEW in Phase 0.5)

Graph/network export for property-graph representations of BCE data.

Key classes and constants:
- `GraphSnapshot` dataclass with `nodes: List[GraphNode]` and `edges: List[GraphEdge]`
- `GraphNode` and `GraphEdge` dataclasses for lightweight graph representation
- Node types: `NODE_TYPE_CHARACTER`, `NODE_TYPE_EVENT`, `NODE_TYPE_SOURCE`
- Edge types: `EDGE_TYPE_CHARACTER_PARTICIPATED_IN_EVENT`, `EDGE_TYPE_CHARACTER_PROFILE_IN_SOURCE`, etc.

Key functions:
- `build_graph_snapshot() -> GraphSnapshot`
  - Builds an in-memory property graph suitable for Neo4j, RDF, or other graph backends

### `bce/search.py` (NEW in Phase 2)

Full-text search across characters and events.

Key functions:
- `search_all(query: str, scope: Optional[List[str]]) -> List[Dict[str, Any]]`
  - Searches traits, references, accounts, notes, and tags
  - Returns structured results with match context
  - Supports scoped searches: `["traits", "references", "accounts", "notes", "tags"]`

### `bce/config.py` (NEW in Phase 0.5)

Configuration management for BCE.

Key class:
- `BceConfig` - Configuration object with environment variable support
  - `data_root: Path` - Path to data directory
  - `cache_size: int` - Maximum cached items (default: 128)
  - `enable_validation: bool` - Enable automatic validation (default: True)
  - `log_level: str` - Logging level (default: WARNING)
  - Properties: `char_dir`, `event_dir`, `sources_file`
  - Method: `validate_paths() -> List[str]`

Environment variables:
- `BCE_DATA_ROOT` - Override data root path
- `BCE_CACHE_SIZE` - Override cache size
- `BCE_ENABLE_VALIDATION` - Enable/disable validation
- `BCE_LOG_LEVEL` - Set log level

Functions:
- `get_default_config() -> BceConfig` - Get singleton config
- `set_default_config(config: BceConfig) -> None` - Set global config
- `reset_default_config() -> None` - Reset to defaults

### `bce/cache.py` (NEW in Phase 0.5)

Cache registry for cache invalidation across modules.

Key class:
- `CacheRegistry` - Registry for cache invalidation callbacks
  - `register(invalidator: Callable[[], None])` - Register cache invalidator
  - `unregister(invalidator: Callable[[], None])` - Unregister invalidator
  - `invalidate_all()` - Invalidate all registered caches
  - `clear_registry()` - Clear all invalidators (for testing)
  - `count() -> int` - Return number of registered invalidators

This replaces the fragile `sys.modules` inspection pattern previously used.

### `bce/exceptions.py` (NEW in Phase 0.5)

Structured exception hierarchy for BCE.

Exception classes:
- `BceError` - Base exception for all BCE errors
- `DataNotFoundError` - Requested data doesn't exist (inherits from FileNotFoundError)
- `ValidationError` - Data validation failed
- `StorageError` - Storage operations failed (inherits from RuntimeError)
- `CacheError` - Cache operations failed
- `ConfigurationError` - Invalid or missing configuration
- `SearchError` - Search operations failed

All exceptions inherit from `BceError`, making it easy to catch any BCE-specific error.

### `bce/sources.py` (NEW in Phase 0.5)

Source metadata management.

Loads and manages source metadata from `bce/data/sources.json`.

Key functions:
- `load_source_metadata(source_id: str) -> SourceMetadata`
- `list_source_ids() -> List[str]`
- Functions for accessing source-level information

### `bce/services.py` (NEW in Phase 0.5)

Service layer providing high-level business logic and orchestration.

(Consult the module directly for current service offerings.)

### `bce/bibles.py` (NEW in Phase 0.5)

Bible text integration for fetching verse text.

Key functions:
- `list_translations() -> List[str]` - List available translations
- `get_verse(book: str, chapter: int, verse: int, translation: str = "web") -> str`
- `get_parallel(book: str, chapter: int, verse: int, translations: List[str]) -> Dict[str, str]`

Enables direct integration of scripture text alongside character/event data.

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
  "tags": ["tag1", "tag2"],
  "relationships": [
    {
      "type": "relationship_type",
      "to": "other_character_id",
      "description": "Relationship description"
    }
  ],
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

**Note**: `tags` and `relationships` fields are optional but recommended for Phase 2+ data.

**Event JSON Structure:**
```json
{
  "id": "event_id",
  "label": "Event Name",
  "participants": ["char_id1", "char_id2"],
  "tags": ["tag1", "tag2"],
  "parallels": [
    {
      "sources": ["mark", "matthew", "luke"],
      "type": "synoptic_parallel",
      "notes": "Optional parallel notes"
    }
  ],
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

**Note**: `tags` and `parallels` fields are optional but recommended for Phase 2+ data.

**Source Metadata JSON Structure** (in `bce/data/sources.json`):
```json
{
  "mark": {
    "source_id": "mark",
    "date_range": "70-75 CE",
    "provenance": "Rome",
    "audience": "Gentile Christians",
    "depends_on": []
  },
  "matthew": {
    "source_id": "matthew",
    "date_range": "80-90 CE",
    "provenance": "Antioch",
    "audience": "Jewish Christians",
    "depends_on": ["mark", "q_source"]
  }
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

### PowerShell Startup Script (`start.ps1`)

Convenience script for Windows PowerShell users:

```powershell
# View character dossier
./start.ps1 character jesus --format markdown

# View event dossier
./start.ps1 event crucifixion --format markdown
```

The script automatically:
- Activates the virtual environment (`.venv`) if present
- Forwards all arguments to `python -m bce.cli`

## Using the BCE API

### Recommended Pattern: Use `bce.api`

**For all external tools, scripts, and integrations, use the `bce.api` module as your primary entry point.**

Example usage:

```python
from bce import api

# Load data
jesus = api.get_character("jesus")
crucifixion = api.get_event("crucifixion")

# List IDs
char_ids = api.list_character_ids()
event_ids = api.list_event_ids()

# Build dossiers
char_dossier = api.build_character_dossier("jesus")
event_dossier = api.build_event_dossier("crucifixion")

# Find conflicts
char_conflicts = api.summarize_character_conflicts("jesus")
event_conflicts = api.summarize_event_conflicts("crucifixion")

# Search
results = api.search_all("resurrection", scope=["traits", "tags"])

# Tag queries
resurrection_chars = api.list_characters_with_tag("resurrection")
resurrection_events = api.list_events_with_tag("resurrection")

# Export data
all_chars = api.export_all_characters()
all_events = api.export_all_events()

# Export to files
api.export_characters_csv("characters.csv")
api.export_events_csv("events.csv")

# Get citations
citations = api.export_citations(format="bibtex")

# Build graph snapshot
graph = api.build_graph_snapshot()
print(f"Graph has {len(graph.nodes)} nodes and {len(graph.edges)} edges")

# Bible text integration
translations = api.list_bible_translations()
verse = api.get_verse_text("John", 3, 16, translation="web")
parallel = api.get_parallel_verse_text("John", 3, 16, translations=["web", "kjv"])
```

### Direct Module Access (Advanced)

Lower-level modules are still available for advanced use cases:
- `bce.queries` - Direct query operations
- `bce.storage` - Raw JSON I/O
- `bce.contradictions` - Conflict detection
- `bce.dossiers` - Dossier builders
- `bce.search` - Search operations

But **prefer `bce.api`** unless you have specific needs that require direct module access.

## Key Patterns for AI Assistants

### 1. When Adding New Characters

1. Create JSON file in `bce/data/characters/<char_id>.json`
2. Follow the character JSON schema exactly
3. Include at least one source_profile
4. **Add `tags` field** with relevant topical tags (Phase 2+)
5. **Add `relationships` field** if the character has documented relationships (Phase 0.5+)
6. Ensure `id` field matches filename (without .json)
7. Run validation: `python -c "from bce.validation import validate_all; print(validate_all())"`
8. Add tests if introducing new patterns

Example minimal character:
```json
{
  "id": "new_character",
  "canonical_name": "New Character",
  "aliases": ["Alternate Name"],
  "roles": ["role1"],
  "tags": ["relevant_tag"],
  "relationships": [],
  "source_profiles": [
    {
      "source_id": "mark",
      "traits": {
        "portrayal": "Brief description"
      },
      "references": ["Mark 1:1"]
    }
  ]
}
```

### 2. When Adding New Events

1. Create JSON file in `bce/data/events/<event_id>.json`
2. Follow the event JSON schema
3. Ensure participant IDs reference existing characters
4. **Add `tags` field** with relevant topical tags (Phase 2+)
5. **Add `parallels` field** for parallel pericopes/accounts (Phase 0.5+)
6. Ensure `id` field matches filename
7. Run validation to check integrity

Example minimal event:
```json
{
  "id": "new_event",
  "label": "New Event",
  "participants": ["character1", "character2"],
  "tags": ["relevant_tag"],
  "parallels": [
    {
      "sources": ["mark", "matthew"],
      "type": "synoptic_parallel",
      "notes": "Similar account in both gospels"
    }
  ],
  "accounts": [
    {
      "source_id": "mark",
      "reference": "Mark 1:1-5",
      "summary": "Brief summary of the event",
      "notes": null
    }
  ]
}
```

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

To generate exports for external tools, use `bce.api`:

```python
from bce import api

# Export all data
all_chars = api.export_all_characters()
all_events = api.export_all_events()

# Export to CSV files
api.export_characters_csv("output/characters.csv")
api.export_events_csv("output/events.csv")

# Export citations
citations = api.export_citations(format="bibtex")

# Build graph snapshot for graph databases
graph = api.build_graph_snapshot()
# graph.nodes: List[GraphNode]
# graph.edges: List[GraphEdge]

# Generate Markdown dossiers
dossier = api.build_character_dossier("jesus")
from bce.export_markdown import dossier_to_markdown
markdown = dossier_to_markdown(dossier)
print(markdown)
```

### 9. Error Handling

Use the structured exception hierarchy for robust error handling:

```python
from bce import api
from bce import exceptions

try:
    char = api.get_character("nonexistent")
except exceptions.DataNotFoundError as e:
    print(f"Character not found: {e}")
except exceptions.BceError as e:
    print(f"BCE error: {e}")

# Configuration errors
try:
    from bce.config import BceConfig
    config = BceConfig(cache_size=-1)
except exceptions.ConfigurationError as e:
    print(f"Invalid configuration: {e}")

# Storage errors
try:
    from bce import storage
    storage.save_character(invalid_character)
except exceptions.StorageError as e:
    print(f"Storage failed: {e}")

# Validation errors
try:
    from bce.validation import validate_all
    errors = validate_all()
    if errors:
        raise exceptions.ValidationError("\n".join(errors))
except exceptions.ValidationError as e:
    print(f"Validation failed: {e}")
```

### 10. Configuration Management

Customize BCE behavior using `BceConfig`:

```python
from pathlib import Path
from bce.config import BceConfig, set_default_config

# Create custom configuration
custom_config = BceConfig(
    data_root=Path("/custom/data/path"),
    cache_size=256,
    enable_validation=True,
    log_level="INFO"
)

# Set as default
set_default_config(custom_config)

# Or use environment variables
# export BCE_DATA_ROOT=/custom/data/path
# export BCE_CACHE_SIZE=256
# export BCE_ENABLE_VALIDATION=true
# export BCE_LOG_LEVEL=INFO

# Get default config
from bce.config import get_default_config
config = get_default_config()
print(config.data_root)
print(config.cache_size)

# Validate paths
errors = config.validate_paths()
if errors:
    print("Configuration errors:", errors)
```

### 11. Search and Tag Queries

Use search and tag features for discovery:

```python
from bce import api

# Full-text search
results = api.search_all("resurrection", scope=["traits", "tags"])
for result in results:
    print(f"{result['type']}: {result['id']} - {result['match_in']}")

# Scoped searches
trait_results = api.search_all("messianic", scope=["traits"])
ref_results = api.search_all("John 3:16", scope=["references"])
tag_results = api.search_all("apocalyptic", scope=["tags"])

# Tag queries
chars_with_tag = api.list_characters_with_tag("resurrection")
events_with_tag = api.list_events_with_tag("passion")

# Check if character has a tag
jesus = api.get_character("jesus")
if "messiah" in jesus.tags:
    print("Jesus is tagged as messiah")
```

## File References in Code

When discussing code locations, use this format:
- `bce/models.py:15-20` for Character dataclass
- `bce/storage.py:64-69` for load_character function
- `bce/queries.py:12-14` for get_character function

## Roadmap Awareness

**Current Status**: Phases 0-4 are **largely complete** as of November 2025.

Completed phases:
- **Phase 0**: Core, Dossiers, Export & Examples ✅
- **Phase 1**: Data Coverage & Validation ✅
  - 62 characters, 10 events
  - Validation suite in place
- **Phase 2**: Thematic Tagging & Query Helpers ✅
  - `tags` field added to Character and Event
  - Tag query helpers: `list_characters_with_tag()`, `list_events_with_tag()`
  - Search with tag-aware scope
- **Phase 3**: Conflict Objects & Ergonomics ✅
  - Normalized conflict summaries: `summarize_character_conflicts()`, `summarize_event_conflicts()`
  - Conflict summaries embedded in dossiers
- **Phase 4**: Stable API Surface for External Tools ✅
  - `bce.api` module provides stable, high-level API
  - Schema documentation in `docs/SCHEMA.md`
  - API tests lock in the public contract

Future work:
- **Phase 5**: Optional Extensions (Proposals only, not yet implemented)
  - HTTP API (FastAPI/Flask)
  - JSON-LD export
  - Additional output formats

See `docs/ROADMAP.md` for complete phase details and implementation status.

## Common Pitfalls to Avoid

1. **USE `bce.api` for external tools**: Always prefer `bce.api` over direct module imports when building external tools or integrations
2. **Don't bypass the query API**: Use `queries.get_character()` instead of `storage.load_character()` to benefit from caching
3. **Don't forget to clear cache**: If manually modifying JSON files, call `queries.clear_cache()` or use `CacheRegistry.invalidate_all()`
4. **Don't create circular dependencies**: Keep imports clean (models → storage → queries → contradictions/dossiers → api)
5. **Don't add UI code**: This is a data engine, not a frontend
6. **Don't hardcode data root paths**: Use `BceConfig` for custom data locations
7. **Don't skip validation**: Always run `validate_all()` after data changes
8. **Handle exceptions properly**: Use the structured exception hierarchy (`BceError`, `DataNotFoundError`, etc.)
9. **Don't ignore new fields**: When adding data, include `tags`, `relationships`, and `parallels` where appropriate

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

# Run specific test file
pytest tests/test_api.py

# List characters
python dev_cli.py list-chars

# View character as markdown (using bce CLI)
bce character jesus --format markdown

# View event as markdown
bce event crucifixion --format markdown

# Validate all data
python -c "from bce.validation import validate_all; print(validate_all() or 'OK')"

# Export everything (legacy dev_cli)
python dev_cli.py export-chars exports/characters.json
python dev_cli.py export-events exports/events.json

# Python API examples
python -c "from bce import api; print(api.list_character_ids())"
python -c "from bce import api; print(len(api.export_all_characters()), 'characters')"
python -c "from bce import api; results = api.search_all('resurrection'); print(len(results), 'results')"

# Environment configuration
export BCE_DATA_ROOT=/path/to/data
export BCE_CACHE_SIZE=256
export BCE_ENABLE_VALIDATION=true
export BCE_LOG_LEVEL=INFO
```

## Additional Documentation

For deeper understanding of specific topics, consult these additional documentation files:

- **`docs/ROADMAP.md`** - Complete project roadmap with implementation status for all phases
- **`docs/SCHEMA.md`** - Detailed schema documentation for API consumers
  - Character and Event model schemas
  - SourceProfile and SourceMetadata schemas
  - CharacterDossier and EventDossier schemas
  - Conflict summary schemas
  - Search result schemas
  - Tag schemas
- **`docs/DATA_ENTRY_GUIDE.md`** - Step-by-step guide for adding new characters and events
- **`docs/features.md`** - Comprehensive feature documentation
- **`CHANGELOG.md`** - Version history and change log
- **`README.md`** - User-facing overview and quickstart guide

---

**Last Updated**: 2025-11-18
**Current Phase**: Phases 0-4 (Largely Complete)
**Python Version**: 3.11+
**Data Files**: 62 characters, 10 events
**Test Coverage**: 74 test functions across 24 test files
**BCE Modules**: 23 Python modules
**Key Architectural Change**: `bce.api` is now the recommended entry point (Phase 4)
