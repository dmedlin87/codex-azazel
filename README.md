# Codex Azazel: BCE (Biblical Character Engine)

> A contradiction-aware Biblical character and event engine focused on New Testament data

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why "Codex Azazel"?

**Azazel** appears in Leviticus 16 as the mysterious recipient of the scapegoat on the Day of Atonement—one goat "for YHWH" (sacrificed), one goat "for Azazel" (sent alive into the wilderness bearing Israel's sins). The name itself is **contested**: Is it a demon? A place? A functional term meaning "goat that goes away"? Scholars genuinely disagree.

In Second Temple literature (1 Enoch, Dead Sea Scrolls, Apocalypse of Abraham), Azazel is **re-mythologized** as a fallen angel and arch-demon, the origin of all sin, bound in the desert awaiting final judgment. Later Jewish and Christian traditions oscillate between treating Azazel as symbol, geography, controlled demon, or even a type of Satan or Christ.

**Azazel is the perfect mascot for this project** because:

- **Diachronic layers**: A single obscure word evolves through radically different interpretations across centuries
- **Source-aware modeling**: Each tradition (Torah, Enochic, Rabbinic, Christian) has its own distinct "Azazel profile"
- **Contested and uncertain**: No single answer exists—honest scholarship must hold multiple possibilities
- **Contradiction-forward**: The conflicts between portrayals are not bugs; they're the whole point

**This project models biblical figures the way scholars actually encounter them: as layered, contested, source-dependent constructions.** Azazel is our flagship demonstration of that approach.

For the full deep-dive, see **[docs/azazel_case_study.md](docs/azazel_case_study.md)** and **[docs/evidence_card_azazel.md](docs/evidence_card_azazel.md)**.

## Overview

**Codex Azazel's BCE** (Biblical Character Engine) is a Python library for modeling New Testament characters and events as structured, source-aware data. It represents per-source profiles (Mark, Matthew, Luke, John, undisputed Paul, Acts, etc.) enabling you to compare portrayals, trace contradictions, and support historical-critical analysis.

All core data lives in JSON format, and the Python API is designed to be simple, pure, and AI-friendly—perfect for both human developers and automated analysis tools.

### Key Capabilities

- **Source-aware modeling**: Track how each Gospel and source portrays characters differently
- **Contradiction detection**: Surface conflicts and differences between parallel accounts
- **Structured exports**: JSON, Markdown, CSV, BibTeX citations, and graph formats
- **Full-text search**: Search across traits, references, accounts, and tags
- **Property graph export**: Build graph snapshots for Neo4j, RDF, or other graph databases
- **Bible text integration**: Fetch verse text from multiple translations
- **Tag-based queries**: Organize and query data by theological and narrative themes

### Current Dataset

- **63 characters** spanning disciples, apostles, antagonists, and supporting figures
  - Including **Azazel** (the project namesake) as a flagship demonstration of multi-profile diachronic modeling
- **10 major events** including the crucifixion, resurrection appearances, and key moments
- **Multiple source perspectives** for comparative analysis

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/dmedlin87/codex-azazel.git
cd codex-azazel

# Install in development mode
pip install -e .[dev]

# Run tests to verify installation
pytest

# Run full validation (respects BCE_ENABLE_VALIDATION)
bce validate-data
```

### Requirements

- Python 3.11 or higher
- Dependencies: None (uses only Python standard library)
- Dev dependencies: pytest, pytest-cov
- Web dependencies (optional): fastapi, uvicorn
- AI dependencies (optional): sentence-transformers, numpy, scikit-learn, torch

### Installing Optional Dependencies

```bash
# For AI-powered features (semantic search, conflict analysis, parallel detection)
pip install -e .[ai]

# For web API server
pip install -e .[web]

# For development and testing (includes AI tests)
pip install -e .[dev,ai]
```

## Quick Start

### CLI Usage

After installation, use the `bce` command for quick inspections:

```bash
# View character dossier as Markdown
bce character jesus --format markdown
bce character paul --format markdown

# View event dossier as Markdown
bce event crucifixion --format markdown
bce event resurrection_appearance --format markdown
```

#### Legacy CLI

The original development CLI is still available:

```bash
# List all characters and events
python dev_cli.py list-chars
python dev_cli.py list-events

# Show specific character or event
python dev_cli.py show-char jesus
python dev_cli.py show-event crucifixion

# Export to JSON
python dev_cli.py export-chars exports/all_characters.json
python dev_cli.py export-events exports/all_events.json
```

### Python API

The recommended entry point for programmatic access is the **`bce.api`** module:

```python
from bce import api

# Load characters and events
jesus = api.get_character("jesus")
crucifixion = api.get_event("crucifixion")

print(f"{jesus.canonical_name} appears in {len(jesus.source_profiles)} sources")
print(f"{crucifixion.label} has {len(crucifixion.accounts)} accounts")

# List all available IDs
char_ids = api.list_character_ids()
event_ids = api.list_event_ids()

# Build comprehensive dossiers
char_dossier = api.build_character_dossier("jesus")
event_dossier = api.build_event_dossier("crucifixion")

# Find contradictions
char_conflicts = api.summarize_character_conflicts("jesus")
event_conflicts = api.summarize_event_conflicts("crucifixion")

# Full-text search
results = api.search_all("resurrection", scope=["traits", "tags"])
for result in results:
    print(f"{result['type']}: {result['id']} - matched in {result['match_in']}")

# Tag-based queries
resurrection_chars = api.list_characters_with_tag("resurrection")
passion_events = api.list_events_with_tag("passion")

# Export all data
all_characters = api.export_all_characters()
all_events = api.export_all_events()

# Export to files
api.export_characters_csv("output/characters.csv")
api.export_events_csv("output/events.csv")

# Get academic citations
citations = api.export_citations(format="bibtex")

# Build property graph snapshot
graph = api.build_graph_snapshot()
print(f"Graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

# Bible text integration
translations = api.list_bible_translations()
verse = api.get_verse_text("John", 3, 16, translation="web")
parallel = api.get_parallel_verse_text("John", 3, 16, translations=["web", "kjv"])
```

For a complete walkthrough, see [`examples/basic_usage.py`](examples/basic_usage.py).

### Web Interface

BCE includes a **polished, modern web interface** for exploring the data interactively:

```bash
# Install web dependencies
pip install -e .[web]

# Start the web server
bce-server

# Or alternatively:
python -m bce.server
```

The web interface will be available at `http://localhost:8000`

#### Web Features

- **Character Browser**: Filterable grid view of 60+ New Testament characters
- **Event Browser**: Compare parallel accounts across different Gospel sources
- **Detailed Dossiers**: Comprehensive character and event pages with conflict highlighting
- **Network Graph**: Interactive D3.js visualization of relationships between characters, events, and sources
- **Full-Text Search**: Search across characters, events, traits, and references
- **Source Comparison**: Side-by-side source analysis with color-coded badges
- **Responsive Design**: Mobile-first design that works on all devices

#### API Documentation

The web server also provides interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

See [`frontend/README.md`](frontend/README.md) for detailed frontend documentation.

## Features

### Core Data Models

BCE centers on a small set of JSON-backed dataclasses:

- **Character**
  - Unique ID, canonical name, aliases, roles
  - Per-source `SourceProfile` objects (one per Gospel/source)
  - Relationships to other characters
  - Topical tags for thematic organization

- **SourceProfile**
  - Source identifier (e.g., "mark", "matthew", "paul_undisputed")
  - Traits dictionary (narrative and theological features)
  - Scripture references

- **Event**
  - Unique ID, display label
  - Participant character IDs
  - Per-source `EventAccount` objects
  - Parallel pericope records
  - Topical tags

- **EventAccount**
  - Source identifier
  - Scripture reference range
  - Summary and optional notes

All models map directly to JSON files and are safe to edit by hand.

### Contradiction Analysis

Detect and analyze differences between source accounts:

```python
from bce import contradictions

# Compare all traits across sources
comparison = contradictions.compare_character_sources("jesus")

# Get only the conflicting traits
conflicts = contradictions.find_trait_conflicts("jesus")

# Find conflicting event accounts
event_conflicts = contradictions.find_events_with_conflicting_accounts("crucifixion")
```

### Export Formats

Export data in multiple formats for different use cases:

- **JSON**: Structured data for web apps and tools
- **Markdown**: Human-readable dossiers and reports
- **CSV**: Tabular data for spreadsheets and analysis
- **BibTeX**: Academic citations for sources
- **Graph**: Property graph snapshots for graph databases

```python
from bce import api

# Export to different formats
api.export_characters_csv("characters.csv")
api.export_events_csv("events.csv")
citations = api.export_citations(format="bibtex")
graph = api.build_graph_snapshot()  # For Neo4j, RDF, etc.
```

### Search and Discovery

Full-text search across all data:

```python
from bce import api

# Search everything
all_results = api.search_all("messiah")

# Scoped searches
trait_results = api.search_all("teacher", scope=["traits"])
ref_results = api.search_all("John 3", scope=["references"])
tag_results = api.search_all("apocalyptic", scope=["tags"])

# Tag-based queries
messiah_chars = api.list_characters_with_tag("messiah")
passion_events = api.list_events_with_tag("passion")
```

### Configuration

Customize BCE behavior with configuration:

```python
from pathlib import Path
from bce.config import BceConfig, set_default_config

# Custom configuration
config = BceConfig(
    data_root=Path("/custom/data/path"),
    cache_size=256,
    enable_validation=True,
    log_level="INFO"
)
set_default_config(config)

# Or use environment variables
# export BCE_DATA_ROOT=/custom/data/path
# export BCE_CACHE_SIZE=256
# export BCE_ENABLE_VALIDATION=true
# export BCE_LOG_LEVEL=INFO
```

## Repository Structure

```text
codex-azazel/
├── bce/                          # Main package (24 modules)
│   ├── __init__.py              # Package exports
│   ├── api.py                   # HIGH-LEVEL API (recommended entry point)
│   ├── server.py                # FastAPI web server (NEW)
│   ├── models.py                # Core dataclasses
│   ├── storage.py               # JSON loading/saving
│   ├── queries.py               # Query API with caching
│   ├── contradictions.py        # Comparison and conflict detection
│   ├── dossiers.py              # Dossier builders
│   ├── dossier_types.py         # TypedDict definitions
│   ├── search.py                # Full-text search
│   ├── export.py                # Main export facade
│   ├── export_json.py           # JSON export
│   ├── export_markdown.py       # Markdown export
│   ├── export_csv.py            # CSV export
│   ├── export_citations.py      # Citation export (BibTeX)
│   ├── export_graph.py          # Graph/network export
│   ├── validation.py            # Data validation
│   ├── config.py                # Configuration management
│   ├── cache.py                 # Cache registry
│   ├── exceptions.py            # Exception hierarchy
│   ├── sources.py               # Source metadata
│   ├── services.py              # Service layer
│   ├── bibles.py                # Bible text integration
│   ├── cli.py                   # Main CLI entry point
│   └── data/
│       ├── characters/          # 63 character JSON files
│       ├── events/              # 10 event JSON files
│       └── sources.json         # Source metadata
├── frontend/                    # Modern web interface (NEW)
│   ├── index.html               # Landing page
│   ├── characters.html          # Character browser
│   ├── character.html           # Character detail page
│   ├── events.html              # Event browser
│   ├── event.html               # Event detail page
│   ├── graph.html               # Network visualization
│   ├── css/
│   │   └── styles.css           # Custom styles
│   └── js/
│       ├── api.js               # API client
│       ├── components.js        # UI components
│       ├── app.js               # Homepage logic
│       └── graph.js             # D3.js visualization
├── tests/                       # Comprehensive test suite (24 files)
├── examples/                    # Usage examples
│   ├── basic_usage.py
│   └── print_dossier_markdown.py
├── docs/
│   ├── ROADMAP.md              # Project roadmap and phases
│   ├── SCHEMA.md               # API schema documentation
│   ├── DATA_ENTRY_GUIDE.md     # Guide for adding data
│   └── features.md             # Feature documentation
├── CLAUDE.md                   # AI assistant guide
├── CHANGELOG.md                # Version history
├── pyproject.toml              # Package configuration
└── README.md                   # This file
```

## Documentation

Comprehensive documentation is available:

- **[ROADMAP.md](docs/ROADMAP.md)** - Project roadmap with implementation status for all phases
- **[SCHEMA.md](docs/SCHEMA.md)** - Detailed API schema documentation for consumers
- **[DATA_ENTRY_GUIDE.md](docs/DATA_ENTRY_GUIDE.md)** - Step-by-step guide for adding new data
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive guide for AI assistants working with this codebase
- **[features.md](docs/features.md)** - Detailed feature documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## Development

### Running Tests

```bash
# Run all tests (excluding AI tests)
pytest

# Run with coverage
pytest --cov=bce

# Run specific test file
pytest tests/test_api.py

# Verbose output
pytest -v

# Run validation pipeline (also available via dev_cli)
bce validate-data

# Run AI-powered feature tests (requires AI dependencies)
# First install: pip install -e .[ai]
pytest tests/test_ai_*.py
```

**Note:** AI-powered tests (semantic search, conflict analysis, parallel detection) require the AI optional dependencies:

```bash
pip install -e .[ai]
```

Without these dependencies, AI tests will fail with `ImportError: sentence-transformers is required for AI features`.

### Data Validation

Always validate data after making changes:

```python
from bce.validation import validate_all

errors = validate_all()
if errors:
    for error in errors:
        print(f"ERROR: {error}")
else:
    print("All validation checks passed!")
```

Or from the command line:

```bash
python -c "from bce.validation import validate_all; print(validate_all() or 'All checks passed!')"
```

### Adding New Data

See **[DATA_ENTRY_GUIDE.md](docs/DATA_ENTRY_GUIDE.md)** for detailed instructions on adding new characters and events.

Quick example:

```json
{
  "id": "new_character",
  "canonical_name": "New Character",
  "aliases": ["Alternative Name"],
  "roles": ["role1", "role2"],
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

## Architecture

### Module Layers

BCE follows a clean layered architecture:

1. **Data Layer**: JSON files in `bce/data/`
2. **Storage Layer**: `storage.py` handles JSON I/O
3. **Query Layer**: `queries.py` provides cached lookups
4. **Analysis Layer**: `contradictions.py`, `search.py`, `dossiers.py`
5. **Export Layer**: Various `export_*.py` modules
6. **API Layer**: `api.py` provides the stable public interface

### Design Principles

- **Simple and explicit**: No magic, clear data structures
- **AI-friendly**: Easy to parse and generate programmatically
- **Human-readable**: JSON and Markdown formats for easy inspection
- **Source-aware**: Every data point tracks its source
- **Contradiction-forward**: Conflicts are features, not bugs
- **Export-oriented**: Easy to get data out in multiple formats

### Core Design Philosophy

BCE is primarily a **data and analysis engine** with the following focus:

- **Data-first approach**: Clean, structured JSON data that can be consumed by any tool
- **Source awareness**: Track and compare how different sources portray the same figures and events
- **Contradiction-forward**: Surface conflicts as valuable data points for scholarship
- **Multiple interfaces**: CLI, Python API, and web interface for different use cases

What BCE explicitly does **NOT** include:

- Debate engine or apologetics logic
- Theological interpretation or commentary
- General-purpose Bible study app features with devotional content
- LLM prompt logic or AI pipelines (though AI features are available as optional extensions)

## Project Status

**Current Version**: 0.1.0
**Status**: Phases 0-4 Complete

BCE has completed the foundational phases of development:

- ✅ **Phase 0**: Core engine, dossiers, exports, and examples
- ✅ **Phase 1**: Data coverage (63 characters, 10 events) and validation
- ✅ **Phase 2**: Thematic tagging and query helpers
- ✅ **Phase 3**: Conflict objects and ergonomics improvements
- ✅ **Phase 4**: Stable API surface for external tools

### Recent Additions

- ✅ **Web Interface**: Modern, responsive web UI with interactive visualizations
- ✅ **REST API**: FastAPI-based HTTP API for web services
- ✅ **Network Visualization**: D3.js-powered graph of relationships

### Future Directions

Potential future enhancements:

- **More coverage**: Additional characters, events, and source perspectives
- **Richer trait vocabulary**: More structured keys for theological and narrative features
- **Extended source coverage**: Pre-canonical texts, apocrypha, church fathers
- **Advanced visualizations**: Timeline views, geographical maps
- **Export enhancements**: JSON-LD, RDF, additional citation formats
- **Progressive Web App**: Offline support and mobile app capabilities

See **[ROADMAP.md](docs/ROADMAP.md)** for detailed phase information.

## Contributing

Contributions are welcome! When contributing:

1. Run tests: `pytest`
2. Validate data: `python -c "from bce.validation import validate_all; print(validate_all())"`
3. Follow existing code style (type hints, dataclasses, docstrings)
4. Add tests for new features
5. Update documentation as needed

See **[CLAUDE.md](CLAUDE.md)** for comprehensive development guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Codex Azazel is designed to support rigorous historical-critical analysis of New Testament texts. The engine surfaces contradictions and differences as valuable data points for scholarship, not as problems to be solved.

---

**Built with**: Python 3.11+ | **Data Format**: JSON | **Philosophy**: Simple, explicit, and AI-friendly
