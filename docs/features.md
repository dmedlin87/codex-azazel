# Feature Proposals for Codex Azazel

This document proposes features that would enhance the Biblical Character Engine beyond the current roadmap. Features are organized by category and priority.

## Priority Legend

- **P0**: Critical for core functionality
- **P1**: High value, natural next step
- **P2**: Valuable but can wait
- **P3**: Nice to have, future consideration

---

## 1. Data Richness & Scholarship Support

### P1: Source Criticism Metadata

**Problem**: Currently we track which source says what, but not *why* or *when* those sources were written.

**Proposal**: Add source metadata to track:
- Estimated dating (e.g., "Mark: 66-70 CE", "John: 90-110 CE")
- Geographic provenance (e.g., "Rome", "Antioch", "Ephesus")
- Intended audience (e.g., "Gentile Christians", "Jewish Christians")
- Literary dependencies (e.g., "Matthew depends on Mark and Q")

**Use case**: Researchers can understand *why* contradictions exist by seeing temporal and cultural contexts.

**Implementation**:
```json
{
  "source_id": "mark",
  "metadata": {
    "date_range": "66-70 CE",
    "provenance": "Rome",
    "audience": "Gentile Christians",
    "depends_on": []
  }
}
```

---

### P1: Parallel Passage Alignment

**Problem**: Synoptic gospels share material but we don't explicitly track which passages are parallel.

**Proposal**: Add a `parallels` field to events and potentially character traits:

```json
{
  "id": "crucifixion",
  "label": "The Crucifixion",
  "parallels": [
    {
      "sources": ["mark", "matthew", "luke", "john"],
      "references": {
        "mark": "Mark 15:22-37",
        "matthew": "Matthew 27:33-50",
        "luke": "Luke 23:33-46",
        "john": "John 19:17-30"
      },
      "relationship": "synoptic_parallel"
    }
  ]
}
```

**Use case**: Scholars studying synoptic problem can easily identify and compare parallel accounts.

---

### P2: Manuscript Variation Tracking

**Problem**: Biblical texts have textual variants that sometimes affect interpretation.

**Proposal**: Track significant manuscript variations for key passages:

```json
{
  "source_id": "mark",
  "traits": {
    "resurrection": "empty tomb with angelic message"
  },
  "references": ["Mark 16:1-8"],
  "textual_notes": {
    "Mark 16:9-20": "Longer ending absent from earliest manuscripts (Sinaiticus, Vaticanus); likely added 2nd century"
  }
}
```

**Use case**: Address questions like "Why does Mark's gospel have different endings?"

---

### P2: Geographic Metadata

**Problem**: Events happen in places, but we don't track locations.

**Proposal**: Add location data to events:

```json
{
  "id": "crucifixion",
  "label": "The Crucifixion",
  "location": {
    "name": "Golgotha",
    "aliases": ["Place of the Skull", "Calvary"],
    "coordinates": {"lat": 31.7784, "lon": 35.2294},
    "modern_name": "Church of the Holy Sepulchre area, Jerusalem"
  }
}
```

**Use case**: Build maps, visualize Jesus's movements, understand geographic patterns.

---

### P3: Chronology/Timeline Support

**Problem**: Events happen in sequence, but we don't track temporal ordering or conflicts in chronology.

**Proposal**: Add temporal metadata:

```json
{
  "id": "crucifixion",
  "chronology": {
    "year_estimate": "30 CE",
    "year_range": "27-33 CE",
    "sequence_after": ["last_supper", "trial_before_pilate"],
    "sequence_before": ["resurrection_appearance"],
    "conflicts": [
      {
        "dimension": "day_of_month",
        "mark": "15 Nisan (Passover)",
        "john": "14 Nisan (day before Passover)"
      }
    ]
  }
}
```

**Use case**: Reconstruct timelines, identify chronological contradictions, understand narrative flow.

---

## 2. Query & Discovery Enhancements

### P1: Full-Text Search

**Problem**: No way to search across all character traits, event accounts, and notes.

**Proposal**: Add search functionality:

```python
from bce.search import search_all

results = search_all("apocalyptic", scope=["traits", "accounts", "notes"])
# Returns: [
#   {"type": "character", "id": "jesus", "match_in": "traits", "source": "mark", ...},
#   {"type": "event", "id": "olivet_discourse", "match_in": "accounts", ...}
# ]
```

**Implementation**: Could use simple string matching initially, upgrade to proper indexing later.

---

### P1: Relationship Graph

**Problem**: Characters interact with each other, but we don't model relationships explicitly.

**Proposal**: Add relationship tracking:

```json
{
  "id": "paul",
  "relationships": [
    {
      "character_id": "barnabas",
      "type": "companion",
      "sources": ["acts"],
      "references": ["Acts 11:25-30", "Acts 13-14"],
      "notes": "Early missionary partner; later separated over Mark"
    },
    {
      "character_id": "peter",
      "type": "colleague_with_conflict",
      "sources": ["paul_undisputed"],
      "references": ["Galatians 2:11-14"],
      "notes": "Confrontation at Antioch over table fellowship"
    }
  ]
}
```

**Use case**: Visualize social networks, understand alliances and conflicts, analyze power dynamics.

---

### P2: Advanced Filtering & Sorting

**Problem**: Limited ways to filter and sort data programmatically.

**Proposal**: Add query builders:

```python
from bce.queries import CharacterQuery

# Find all characters who appear in Paul's letters but not the gospels
results = (CharacterQuery()
    .has_source("paul_undisputed")
    .excludes_source("mark", "matthew", "luke", "john")
    .execute())

# Find all events with high-conflict accounts
results = (EventQuery()
    .has_conflicts()
    .conflict_severity("high")
    .participant("jesus")
    .execute())
```

---

### P2: Statistical Analysis Tools

**Problem**: Hard to answer questions like "How often does Mark mention 'kingdom'?" or "Which source emphasizes suffering most?"

**Proposal**: Add analytical functions:

```python
from bce.analytics import trait_frequency, source_stats

# Count trait mentions across sources
freq = trait_frequency("kingdom_of_god")
# Returns: {"mark": 14, "matthew": 5, "luke": 32, "john": 2}

# Get source statistics
stats = source_stats("mark")
# Returns: {
#   "character_count": 45,
#   "event_count": 28,
#   "unique_traits": 87,
#   "total_references": 234
# }
```

---

## 3. Data Quality & Validation

### P1: Reference Validation

**Problem**: Scripture references are free-form strings; no validation that they're well-formed or exist.

**Proposal**: Add reference parser and validator:

```python
from bce.validation import validate_reference

result = validate_reference("Mark 16:1-8")
# Returns: {
#   "valid": True,
#   "book": "Mark",
#   "chapter": 16,
#   "verse_start": 1,
#   "verse_end": 8,
#   "canonical": True
# }

result = validate_reference("Mark 99:1")
# Returns: {"valid": False, "error": "Mark has only 16 chapters"}
```

**Implementation**: Use existing Bible structure data (books, chapters, verse counts).

---

### P1: Cross-Reference Validation

**Problem**: Events reference character IDs, but we don't validate that those characters actually exist or have relevant source profiles.

**Proposal**: Enhance validation to check:
- All event participants exist as characters
- Event accounts reference sources that participants have profiles for
- No orphaned references or broken links

```python
from bce.validation import validate_cross_references

errors = validate_cross_references()
# Returns: [
#   "Event 'temple_cleansing' participant 'money_changers' not found in characters",
#   "Event 'crucifixion' account from 'thomas' but participant 'jesus' has no 'thomas' profile"
# ]
```

---

### P2: Data Completeness Reports

**Problem**: Hard to know which characters/events need more data.

**Proposal**: Add completeness scoring:

```python
from bce.analytics import completeness_report

report = completeness_report("jesus")
# Returns: {
#   "overall_score": 0.75,
#   "has_aliases": True,
#   "has_roles": True,
#   "source_count": 4,
#   "avg_traits_per_source": 3.5,
#   "missing": ["relationships", "chronology"],
#   "recommendations": ["Add more Pauline traits", "Include Gospel of John profile"]
# }
```

---

### P2: Automated Consistency Checks

**Problem**: Data entry errors can create logical inconsistencies.

**Proposal**: Add consistency validators:
- Check that inverse relationships match (if A mentions B, does B mention A?)
- Verify event chronology doesn't have loops
- Ensure source IDs are consistent across all files
- Detect duplicate aliases across characters

---

## 4. Export & Interoperability

### P1: Graph Database Export

**Problem**: The data is inherently graph-like (characters → events → sources) but only exports to flat JSON.

**Proposal**: Add Neo4j/RDF export:

```python
from bce.export import export_to_neo4j, export_to_rdf

# Export to Neo4j
export_to_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Export to RDF/Turtle
export_to_rdf("output/codex.ttl", format="turtle")
```

**Use case**: Scholars can use graph query languages (Cypher, SPARQL) for complex analysis.

---

### P1: Citation Export (BibTeX, CSL)

**Problem**: Scholars need to cite sources properly.

**Proposal**: Generate citation-ready exports:

```python
from bce.export import export_citations

citations = export_citations(format="bibtex")
# Returns BibTeX entries for all sources, characters, and events
# Useful for academic papers
```

---

### P2: CSV/Spreadsheet Export

**Problem**: Non-programmers want to explore data in Excel/Google Sheets.

**Proposal**: Add CSV exporters:

```python
from bce.export import export_characters_csv

export_characters_csv("characters.csv", include_fields=["id", "name", "roles", "source_count"])
# Creates spreadsheet-friendly format with one row per character
```

---

### P2: API Integration (Bible Gateway, ESV, etc.)

**Problem**: We reference scripture but don't include the actual text.

**Proposal**: Add integrations to fetch referenced text:

```python
from bce.integrations import fetch_scripture_text

text = fetch_scripture_text("Mark 1:9-11", translation="NRSV")
# Returns: "In those days Jesus came from Nazareth of Galilee..."
```

**Note**: Requires API keys and respecting usage limits/licensing.

---

### P3: Linked Data / JSON-LD Export

**Problem**: Not compatible with Semantic Web standards.

**Proposal**: Export as JSON-LD with proper ontologies:

```json
{
  "@context": "http://www.cidoc-crm.org/cidoc-crm/",
  "@type": "E21_Person",
  "rdfs:label": "Jesus of Nazareth",
  "P98i_was_born": {
    "@type": "E67_Birth",
    "P7_took_place_at": {
      "@type": "E53_Place",
      "rdfs:label": "Bethlehem"
    }
  }
}
```

---

## 5. Developer Experience

### P1: Dataclass Helper Methods

**Problem**: Working with dataclasses is verbose; need helper methods.

**Proposal**: Add utility methods to models:

```python
from bce.models import Character

jesus = get_character("jesus")

# Current: loop through source_profiles manually
# Proposed:
mark_profile = jesus.get_source_profile("mark")
all_sources = jesus.list_sources()
has_trait = jesus.has_trait("resurrection", source="mark")
```

---

### P1: Batch Operations

**Problem**: No efficient way to load/save multiple characters at once.

**Proposal**: Add batch loaders:

```python
from bce.storage import load_characters_batch, save_characters_batch

# Load multiple at once
chars = load_characters_batch(["jesus", "paul", "peter"])

# Save multiple
save_characters_batch([char1, char2, char3])
```

---

### P2: Data Import Tools

**Problem**: Adding new data means manually writing JSON.

**Proposal**: Add import helpers:

```python
from bce.import_tools import CharacterBuilder

builder = (CharacterBuilder("mary_magdalene")
    .set_name("Mary Magdalene")
    .add_alias("Mary of Magdala")
    .add_role("disciple")
    .add_source_profile(
        source_id="mark",
        traits={"role": "first witness to resurrection"},
        references=["Mark 16:1-9"]
    )
    .save())
```

---

### P2: Interactive Shell/REPL Enhancements

**Problem**: Exploring data programmatically is cumbersome.

**Proposal**: Add IPython/Jupyter integration:

```python
# bce/repl.py
from bce import *

def explore():
    """Launch interactive exploration session with pre-loaded utilities"""
    import IPython
    IPython.embed(
        banner1="Codex Azazel REPL - Type 'help()' for available commands",
        user_ns=globals()
    )
```

Usage: `bce repl` launches interactive session.

---

### P3: GraphQL API Layer

**Problem**: REST APIs are rigid; clients often over-fetch or under-fetch.

**Proposal**: Add GraphQL endpoint:

```graphql
query {
  character(id: "jesus") {
    canonicalName
    sourceProfiles {
      sourceId
      traits
    }
    events {
      label
      conflicts
    }
  }
}
```

**Note**: This conflicts a bit with "no HTTP API" non-goal, but GraphQL could be local-only via CLI.

---

## 6. Conflict Analysis Enhancements

### P1: Conflict Severity Scoring

**Problem**: Not all contradictions are equal; some are minor, some are fundamental.

**Proposal**: Add severity classification:

```python
{
  "conflict_id": "jesus:resurrection:mark_vs_matthew",
  "severity": "medium",
  "category": "narrative_detail",
  "impact": "affects historical reconstruction but not core theology",
  "sources_agree_count": 0,
  "sources_disagree_count": 2
}
```

Severity levels:
- **low**: Minor details (e.g., exact wording of inscription)
- **medium**: Significant narrative differences (e.g., resurrection appearances)
- **high**: Fundamental theological differences (e.g., Jesus's nature)

---

### P1: Conflict Categories/Taxonomy

**Problem**: Conflicts aren't categorized by type.

**Proposal**: Add conflict taxonomy:

```python
{
  "conflict_id": "...",
  "category": "chronological",  # or: theological, geographical, narrative, numerical
  "subcategory": "event_sequence",
  "description": "Order of temple cleansing differs between synoptics and John"
}
```

---

### P2: Harmonization Attempts Tracking

**Problem**: Scholars have proposed harmonizations; we don't track them.

**Proposal**: Add optional harmonization field:

```python
{
  "conflict_id": "jesus:birth_narrative:matthew_vs_luke",
  "harmonizations": [
    {
      "approach": "sequential",
      "description": "Magi visited after family returned from Egypt to Nazareth, before settling",
      "proponents": ["Augustine", "Calvin"],
      "weaknesses": ["Requires Luke's census in 6 CE to be same as Matthew's birth under Herod who died 4 BCE"]
    }
  ]
}
```

---

### P3: Conflict Resolution Patterns

**Problem**: Different interpretive strategies exist for handling contradictions.

**Proposal**: Document and categorize resolution approaches:

```python
{
  "conflict_id": "...",
  "resolution_strategies": [
    {
      "strategy": "inerrantist_harmonization",
      "description": "Both accounts are historically accurate; details complement rather than contradict"
    },
    {
      "strategy": "source_criticism",
      "description": "Matthew and Luke used different sources (M and L); contradictions reflect source differences"
    },
    {
      "strategy": "theological_priority",
      "description": "Authors prioritized theological message over historical precision"
    }
  ]
}
```

---

## 7. Performance & Scalability

### P2: Database Backend Option

**Problem**: JSON files won't scale to thousands of characters/events.

**Proposal**: Add optional SQLite/PostgreSQL backend:

```python
from bce.storage import configure_backend

# Use SQLite instead of JSON
configure_backend("sqlite:///codex.db")

# Everything else works the same
jesus = get_character("jesus")
```

**Note**: Keep JSON as default for simplicity, but allow DB for large datasets.

---

### P2: Incremental Loading

**Problem**: Loading all characters/events at once is slow.

**Proposal**: Already have `iter_characters()`, but add lazy loading:

```python
from bce.queries import lazy_load

# Don't load everything upfront
characters = lazy_load("characters")

# Load on demand
for char in characters:
    if "apocalyptic" in char.tags:
        process(char)
```

---

### P3: Caching Strategy Improvements

**Problem**: `@lru_cache` is simple but not configurable.

**Proposal**: Add cache configuration:

```python
from bce.cache import configure_cache

configure_cache(
    backend="redis",  # or "memory", "disk"
    max_size=1000,
    ttl=3600
)
```

---

## 8. Documentation & Education

### P1: Data Entry Guide

**Problem**: Contributors don't know how to add quality data.

**Proposal**: Create `docs/DATA_ENTRY_GUIDE.md` with:
- How to research a character/event
- What sources to consult
- How to identify contradictions
- Examples of good vs. poor data entries
- Common pitfalls

---

### P1: Example Use Cases

**Problem**: Users don't know what the engine is good for.

**Proposal**: Add `examples/` for common tasks:
- `examples/synoptic_comparison.py` - Compare parallel passages
- `examples/conflict_report.py` - Generate conflict analysis report
- `examples/character_network.py` - Build social network graph
- `examples/source_bias_analysis.py` - Analyze source tendencies

---

### P2: Jupyter Notebooks

**Problem**: Visual exploration is more accessible than code.

**Proposal**: Add `notebooks/`:
- `notebooks/getting_started.ipynb` - Introduction to BCE
- `notebooks/conflict_analysis.ipynb` - Interactive conflict exploration
- `notebooks/synoptic_problem.ipynb` - Visualizing gospel relationships

---

### P3: Video Tutorials

**Problem**: Some users prefer video content.

**Proposal**: Create screencast tutorials:
- "Getting started with Codex Azazel"
- "Adding a new character"
- "Analyzing contradictions"
- "Exporting data for research"

---

## 9. Community & Contribution

### P1: Contribution Guidelines

**Problem**: No clear process for contributions.

**Proposal**: Create `CONTRIBUTING.md` with:
- Code style requirements
- Test expectations
- PR template
- Review process
- Data quality standards

---

### P2: Data Review Workflow

**Problem**: Need expert review for biblical data accuracy.

**Proposal**: Add review system:
- Label PRs as "needs-scholar-review"
- Maintain list of volunteer reviewers
- Use GitHub Discussions for data debates

---

### P3: Plugin System

**Problem**: Users want custom functionality without modifying core.

**Proposal**: Add plugin architecture:

```python
# plugins/my_analysis.py
from bce.plugins import register_analyzer

@register_analyzer("custom_conflict_scorer")
def my_scorer(conflict):
    return calculate_score(conflict)
```

Load plugins: `bce --plugin my_analysis character jesus`

---

## Implementation Priorities

Based on impact and alignment with project goals:

**Immediate (P0-P1):**
1. Source criticism metadata
2. Parallel passage alignment
3. Full-text search
4. Reference validation
5. Relationship graph
6. Citation export
7. Dataclass helper methods

**Near-term (P1-P2):**
1. Geographic metadata
2. Conflict severity scoring
3. Graph database export
4. Data completeness reports
5. CSV export
6. Data entry guide

**Future (P2-P3):**
1. Chronology support
2. Manuscript variation tracking
3. Statistical analysis
4. Database backend
5. Plugin system
6. GraphQL API

---

## Questions for Project Direction

1. **Scope boundaries**: How much interpretive/theological metadata should we include vs. just raw source data?

2. **Academic rigor**: Should we require peer review for data entries? Citation requirements?

3. **Target audience**: Optimize for scholars, developers, or general public?

4. **Licensing**: How to handle scripture text integration given copyright constraints?

5. **Expansion**: Stay focused on NT, or eventually include OT, apocrypha, church fathers, etc.?

6. **Neutrality**: Should the engine take stances on historical questions, or remain purely descriptive?

---

**Last Updated**: 2025-11-17
**Status**: Proposal document
**Feedback**: Open for discussion and revision
