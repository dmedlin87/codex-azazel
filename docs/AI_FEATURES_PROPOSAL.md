# AI Features Proposal for Codex Azazel

**Date**: 2025-11-18
**Status**: Proposal
**Target Phase**: 6+ (Post-Stable API)

## Overview

This document proposes AI-powered features that enhance Codex Azazel's core mission as a **data and analysis engine** for New Testament characters and events. All proposals respect the project's explicit non-goals: no UI, no debate engine, no apologetics, and no baked-in LLM prompt logic.

Instead, these features focus on:

- **Data quality improvement** - Help maintain accurate, consistent, and complete data
- **Enhanced analysis** - Surface deeper insights from existing data
- **Discovery and exploration** - Help users find patterns and connections
- **Data extraction** - Accelerate data entry from source texts

## Guiding Principles

1. **Data-centric**: AI features should improve the quality and utility of BCE's data
2. **Tool-friendly**: Output structured, machine-readable results for downstream tools
3. **Transparent**: AI outputs should be inspectable, not black boxes
4. **Optional**: AI features should enhance, not replace, core functionality
5. **Respect boundaries**: No apologetics, debate logic, or theological arguments

---

## Proposed Features

### Category 1: Data Quality & Validation

#### 1.1 AI-Assisted Contradiction Detection

**Current State**: `bce/contradictions.py` uses exact string matching to detect conflicts.

**Enhancement**: Use semantic similarity to detect contradictions that differ in wording but align in meaning, and flag genuine conflicts vs. complementary details.

**API Design**:

```python
from bce.ai import semantic_contradictions

# Analyze trait conflicts with semantic understanding
results = semantic_contradictions.analyze_character_traits(
    "jesus",
    model="local",  # or "api" for external LLM
)

# Returns structured output
{
    "trait": "messianic_self_understanding",
    "sources": {
        "mark": "Avoids messianic titles publicly",
        "john": "Explicitly claims divinity and messianic status"
    },
    "semantic_analysis": {
        "is_genuine_conflict": True,
        "conflict_type": "theological_emphasis",
        "similarity_score": 0.23,
        "explanation": "Mark emphasizes messianic secret while John presents overt claims",
        "severity": "high"
    }
}
```

**Implementation Notes**:

- Use sentence embeddings (e.g., all-MiniLM-L6-v2) for local/offline analysis
- Optional: Support API-based models (GPT 5.1) for deeper analysis
- Store results in a separate `ai_analysis/` directory, not in core data
- Exportable via `bce.api.export_ai_contradiction_analysis()`

---

#### 1.2 Data Completeness Auditor

**Purpose**: Identify gaps, inconsistencies, and areas needing expansion.

**API Design**:

```python
from bce.ai import completeness

# Audit all characters
report = completeness.audit_characters()

# Returns structured report
{
    "character_id": "thomas",
    "completeness_score": 0.65,
    "gaps": [
        {
            "type": "missing_source_profile",
            "source": "luke",
            "priority": "medium",
            "suggestion": "Thomas appears in Luke 24:33-49 but lacks a Luke profile"
        },
        {
            "type": "sparse_traits",
            "source": "john",
            "priority": "low",
            "suggestion": "John profile has only 2 traits; consider adding more detail"
        }
    ],
    "inconsistencies": [
        {
            "type": "tag_mismatch",
            "issue": "Character participates in resurrection events but lacks 'resurrection' tag",
            "priority": "low"
        }
    ]
}
```

**Benefits**:

- Systematic quality improvement
- Prioritized data entry tasks
- Consistency across the dataset

---

#### 1.3 Smart Validation Suggestions

**Purpose**: Use AI to suggest fixes for validation errors.

**API Design**:

```python
from bce.ai import validation_assistant

# Get AI suggestions for validation errors
errors = validation.validate_all()
suggestions = validation_assistant.suggest_fixes(errors)

# Returns actionable suggestions
[
    {
        "error": "Character 'bartholomew' references unknown event 'calling_of_nathanael'",
        "suggestion": "Create event 'calling_of_nathanael' or use existing 'calling_of_disciples'",
        "confidence": 0.85,
        "similar_events": ["calling_of_disciples", "calling_of_first_disciples"]
    }
]
```

---

### Category 2: Enhanced Search & Discovery

#### 2.1 Semantic Search

**Current State**: `bce/search.py` uses case-insensitive substring matching.

**Enhancement**: Enable conceptual queries that understand meaning, not just keywords.

**API Design**:

```python
from bce.ai import semantic_search

# Search by concept, not just keywords
results = semantic_search.query(
    "characters who doubt but later believe",
    top_k=5,
    scope=["traits", "relationships"]
)

# Returns ranked results with explanations
[
    {
        "type": "character",
        "id": "thomas",
        "relevance_score": 0.92,
        "matching_context": "Trait 'doubt_and_belief' in John: 'Refuses to believe without physical proof but confesses Jesus as Lord'",
        "explanation": "Strong match: explicitly depicts doubt followed by confession"
    },
    {
        "type": "character",
        "id": "peter",
        "relevance_score": 0.78,
        "matching_context": "Relationship with Jesus: denial followed by restoration",
        "explanation": "Moderate match: shows failure and restoration pattern"
    }
]
```

**Implementation**:

- Build searchable index using sentence embeddings
- Cache embeddings to avoid recomputation
- Update index automatically when data changes
- Fallback to keyword search if AI unavailable

---

#### 2.2 Thematic Clustering

**Purpose**: Automatically discover thematic groupings across characters and events.

**API Design**:

```python
from bce.ai import clustering

# Discover thematic clusters
clusters = clustering.find_character_clusters(
    num_clusters=8,
    basis=["traits", "tags", "roles"]
)

# Returns clusters with interpretable labels
[
    {
        "cluster_id": "apocalyptic_figures",
        "label": "Apocalyptic and Eschatological Figures",
        "members": ["jesus", "john_the_baptist", "paul"],
        "representative_traits": [
            "kingdom of god proclamation",
            "end times urgency",
            "prophetic authority"
        ],
        "confidence": 0.87
    }
]
```

**Use Cases**:

- Auto-generate tag suggestions
- Discover unexpected connections
- Export clusters for visualization tools

---

#### 2.3 Question Answering over Data

**Purpose**: Answer structured questions about the dataset.

**API Design**:

```python
from bce.ai import qa

# Ask questions in natural language
answer = qa.ask("Which gospels portray Jesus as most divine?")

# Returns structured answer with evidence
{
    "answer": "The Gospel of John presents the most explicit divine Christology",
    "confidence": 0.91,
    "evidence": [
        {
            "character": "jesus",
            "source": "john",
            "trait": "divine_claims",
            "value": "Explicitly claims pre-existence and unity with God",
            "reference": "John 1:1-18, 8:58, 10:30"
        }
    ],
    "comparison": {
        "john": {"divine_emphasis": "high", "explicit_claims": True},
        "mark": {"divine_emphasis": "low", "explicit_claims": False},
        "matthew": {"divine_emphasis": "medium", "explicit_claims": False},
        "luke": {"divine_emphasis": "medium", "explicit_claims": False}
    }
}
```

**Important**: This is NOT apologetics or debate. It's data retrieval with cited evidence.

---

### Category 3: Data Extraction & Entry Assistance

#### 3.1 Automated Trait Extraction

**Purpose**: Extract character traits and event details from scripture references.

**API Design**:

```python
from bce.ai import extraction

# Extract traits from a scripture passage
traits = extraction.extract_character_traits(
    character_id="nicodemus",
    source="john",
    passage="John 3:1-21",
    bible_text="<full text of John 3:1-21>"
)

# Returns suggested traits for human review
{
    "character_id": "nicodemus",
    "source": "john",
    "reference": "John 3:1-21",
    "suggested_traits": [
        {
            "trait_key": "social_status",
            "trait_value": "Pharisee and member of the Jewish ruling council",
            "confidence": 0.95,
            "evidence": "John 3:1 - 'a man of the Pharisees named Nicodemus, a member of the Jewish ruling council'"
        },
        {
            "trait_key": "spiritual_seeking",
            "trait_value": "Comes to Jesus at night seeking understanding",
            "confidence": 0.88,
            "evidence": "John 3:2 - 'He came to Jesus at night'"
        }
    ],
    "needs_review": True
}
```

**Workflow**:

1. AI extracts suggested traits
2. Human reviewer approves/edits
3. Approved traits added to character JSON
4. Maintains data quality through human oversight

---

#### 3.2 Parallel Passage Detection

**Purpose**: Automatically identify synoptic parallels and variant accounts.

**API Design**:

```python
from bce.ai import parallels

# Find parallel passages across sources
parallel_set = parallels.detect_event_parallels(
    event_id="feeding_of_5000"
)

# Returns parallel pericopes with similarity analysis
{
    "event_id": "feeding_of_5000",
    "parallels": [
        {
            "sources": ["mark", "matthew", "luke"],
            "type": "synoptic_parallel",
            "references": {
                "mark": "Mark 6:30-44",
                "matthew": "Matthew 14:13-21",
                "luke": "Luke 9:10-17"
            },
            "similarity_score": 0.94,
            "narrative_overlap": "high",
            "suggested_summary": "Jesus feeds 5000 with five loaves and two fish in deserted place"
        },
        {
            "sources": ["john"],
            "type": "johannine_variant",
            "references": {"john": "John 6:1-15"},
            "similarity_score": 0.78,
            "narrative_overlap": "medium",
            "notes": "Includes unique Johannine theological framing (bread of life discourse)"
        }
    ]
}
```

**Benefits**:

- Faster population of `parallels` field in event JSON
- Discover parallels not immediately obvious
- Suggest updates to existing parallel records

---

#### 3.3 Relationship Inference

**Purpose**: Suggest potential relationships based on co-occurrence and textual evidence.

**API Design**:

```python
from bce.ai import relationships

# Infer potential relationships for a character
suggestions = relationships.infer_for_character("martha_of_bethany")

# Returns suggested relationships with evidence
[
    {
        "character_id": "lazarus_of_bethany",
        "suggested_type": "sibling",
        "confidence": 0.97,
        "evidence": [
            "Co-occur in John 11:1-44",
            "John 11:1 - 'Now a man named Lazarus was sick. He was from Bethany, the village of Mary and her sister Martha'",
            "Shared location and family context"
        ],
        "already_exists": False
    },
    {
        "character_id": "mary_of_bethany",
        "suggested_type": "sibling",
        "confidence": 0.97,
        "evidence": ["John 11:1 explicitly names them as sisters"],
        "already_exists": True
    }
]
```

---

### Category 4: Export & Integration Enhancements

#### 4.1 Natural Language Dossier Summaries

**Purpose**: Generate readable narrative summaries from structured dossiers.

**API Design**:

```python
from bce.ai import summaries

# Generate narrative summary from dossier
dossier = api.build_character_dossier("paul")
summary = summaries.generate_character_summary(
    dossier,
    style="academic",  # or "accessible", "technical"
    max_words=200
)

# Returns formatted narrative
"""
Paul of Tarsus appears in Acts and his undisputed epistles as a
transformative figure in early Christianity. Sources depict significant
contradictions in his relationship to Jewish law: Acts presents him as
Torah-observant (Acts 21:20-26), while his letters emphasize freedom
from law for Gentile believers (Galatians 3:23-29). His Damascus road
encounter marks a theological pivot from persecutor to apostle. Source
profiles reveal tensions between Acts' heroic narrative and Paul's own
self-presentation in the epistles regarding authority, suffering, and
apostolic credentials.
"""
```

**Use Cases**:

- Quick overviews for external tools
- Export to documentation
- Generate README snippets

---

#### 4.2 Citation Generation

**Purpose**: Auto-generate academic citations for characters and events.

**API Design**:

```python
from bce.ai import citations

# Generate citation for character usage
cite = citations.generate_character_citation(
    "jesus",
    usage_context="analysis of messianic self-understanding",
    format="chicago"
)

# Returns formatted citation
"""
Codex Azazel Biblical Character Engine. "Jesus of Nazareth:
Multi-Source Profile." Accessed November 18, 2025. Character dossier
aggregating profiles from Mark, Matthew, Luke, John, Acts, and Pauline
epistles. https://github.com/dmedlin87/codex-azazel/blob/main/bce/data/characters/jesus.json
"""
```

---

### Category 5: Advanced Analytics

#### 5.1 Source Tendency Analysis

**Purpose**: Identify systematic patterns in how sources portray characters/events.

**API Design**:

```python
from bce.ai import source_analysis

# Analyze tendencies across a source
tendencies = source_analysis.analyze_source_patterns("mark")

# Returns systematic patterns
{
    "source_id": "mark",
    "character_portrayal_patterns": [
        {
            "pattern": "messianic_secrecy",
            "frequency": "high",
            "characters_affected": ["jesus"],
            "evidence": "Consistent trait across Jesus profile emphasizing hidden identity",
            "theological_significance": "Markan theme of gradual revelation"
        },
        {
            "pattern": "disciple_misunderstanding",
            "frequency": "high",
            "characters_affected": ["peter", "james_son_of_zebedee", "john"],
            "evidence": "Traits show repeated failure to comprehend Jesus's mission"
        }
    ],
    "narrative_priorities": [
        "suffering_christology",
        "apocalyptic_urgency",
        "discipleship_failure"
    ]
}
```

**Benefits**:

- Understand source-level theological tendencies
- Guide trait vocabulary development
- Export for historical-critical analysis tools

---

#### 5.2 Contradiction Severity Scoring

**Current State**: `bce/contradictions.py` has basic severity estimation.

**Enhancement**: Use AI to assess theological, historical, and narrative significance of conflicts.

**API Design**:

```python
from bce.ai import conflict_analysis

# Enhanced contradiction analysis
analysis = conflict_analysis.assess_conflict(
    character_id="jesus",
    trait="resurrection_appearances_timeline"
)

# Returns detailed assessment
{
    "trait": "resurrection_appearances_timeline",
    "basic_severity": "high",  # from existing logic
    "ai_assessment": {
        "theological_significance": "high",
        "historical_significance": "medium",
        "narrative_coherence_impact": "low",
        "explanation": "Discrepancies in appearance sequence and location reflect different theological priorities rather than coordinated chronology",
        "scholarly_consensus": "Widely acknowledged as source-specific emphasis",
        "implications": [
            "Reflects independent traditions",
            "May indicate oral transmission variants",
            "Each gospel prioritizes different witnesses"
        ]
    }
}
```

---

#### 5.3 Event Reconstruction

**Purpose**: Synthesize multi-source event accounts into comparative timeline.

**API Design**:

```python
from bce.ai import reconstruction

# Build comparative event reconstruction
timeline = reconstruction.build_event_timeline("crucifixion")

# Returns structured comparison
{
    "event_id": "crucifixion",
    "timeline_elements": [
        {
            "element": "time_of_crucifixion",
            "sources": {
                "mark": "third hour (9 AM)",
                "john": "about the sixth hour (noon)"
            },
            "conflict": True,
            "ai_analysis": "Temporal discrepancy potentially reflects different reckoning systems or theological symbolism (John's Passover lamb chronology)"
        },
        {
            "element": "jesus_final_words",
            "sources": {
                "mark": "My God, my God, why have you forsaken me?",
                "luke": "Father, into your hands I commit my spirit",
                "john": "It is finished"
            },
            "conflict": True,
            "ai_analysis": "Each gospel preserves different final sayings, reflecting distinct theological emphases"
        }
    ],
    "synthesis": "Multi-source comparison reveals significant chronological and narrative variations..."
}
```

---

## Implementation Strategy

### Phase 6.1: Foundation (Core AI Infrastructure)

**Goals**:

- Establish AI module structure under `bce/ai/`
- Implement local/offline-first models (sentence embeddings)
- Create caching and index management
- Add configuration for optional AI features

**Deliverables**:

```text
bce/ai/
  __init__.py
  config.py          # AI feature configuration
  embeddings.py      # Sentence embedding utilities
  cache.py           # AI-specific caching
  models.py          # Model loading and management
```

**Configuration**:

```python
# bce.config.BceConfig additions
class BceConfig:
    enable_ai_features: bool = False
    ai_model_backend: str = "local"  # "local", "openai", "anthropic"
    ai_cache_dir: Path = data_root / "ai_cache"
    embedding_model: str = "all-MiniLM-L6-v2"
```

---

### Phase 6.2: Data Quality Features

**Implement**:

- AI-assisted contradiction detection (1.1)
- Data completeness auditor (1.2)
- Smart validation suggestions (1.3)

**API Surface** (`bce.api` additions):

```python
def analyze_semantic_contradictions(char_id: str) -> Dict[str, Any]
def audit_character_completeness(char_id: Optional[str] = None) -> Dict[str, Any]
def get_validation_suggestions(errors: List[str]) -> List[Dict[str, Any]]
```

---

### Phase 6.3: Enhanced Search

**Implement**:

- Semantic search (2.1)
- Thematic clustering (2.2)
- Question answering (2.3)

**API Surface**:

```python
def semantic_search(query: str, top_k: int = 10) -> List[Dict[str, Any]]
def find_thematic_clusters(num_clusters: int = 8) -> List[Dict[str, Any]]
def ask_question(question: str) -> Dict[str, Any]
```

---

### Phase 6.4: Data Extraction Tools

**Implement**:

- Automated trait extraction (3.1)
- Parallel passage detection (3.2)
- Relationship inference (3.3)

**Usage Pattern**:

```bash
# CLI for data entry assistance
bce ai extract-traits --character nicodemus --source john --reference "John 3:1-21" --review

# Outputs suggested traits to stdout for review
# Use --apply flag to automatically add to character JSON (with confirmation)
```

---

### Phase 6.5: Export & Analytics

**Implement**:

- Natural language summaries (4.1)
- Enhanced citations (4.2)
- Source tendency analysis (5.1)
- Advanced conflict analysis (5.2)

---

## Technical Considerations

### Model Selection

**Local/Offline Options** (Recommended for core features):

- **Sentence embeddings**: `all-MiniLM-L6-v2` (small, fast, good quality)
- **Text generation**: `Llama 3.1 8B` or `Phi-3` (via Ollama)
- **Classification**: Fine-tuned BERT models for specific tasks

**API-Based Options** (Optional, for advanced features):
- **OpenAI**: GPT 5.1 for complex reasoning tasks and long-context analysis
- **Configurable per feature**: Allow users to choose backend

### Performance & Caching

- **Embedding cache**: Store embeddings for all traits/references
- **Incremental updates**: Only recompute embeddings for changed data
- **Background indexing**: Build search indices asynchronously
- **Cache invalidation**: Integrate with existing `bce.cache.CacheRegistry`

### Data Privacy & Ethics

- **No external transmission by default**: All features work offline
- **Explicit opt-in for API calls**: User must configure API keys
- **Transparent AI outputs**: All AI-generated content marked as such
- **Human-in-the-loop**: Critical updates require human approval

---

## Export Formats for AI Features

### AI Analysis Export Structure

```json
{
  "metadata": {
    "generated_at": "2025-11-18T12:00:00Z",
    "bce_version": "0.6.0",
    "ai_model": "all-MiniLM-L6-v2",
    "feature": "semantic_contradiction_analysis"
  },
  "character_id": "jesus",
  "analysis": {
    "trait": "messianic_self_understanding",
    "is_genuine_conflict": true,
    "severity": "high",
    "explanation": "...",
    "evidence": [...]
  }
}
```

**Storage**: All AI outputs stored separately in `bce/data/ai_analysis/` and excluded from core data validation.

---

## Testing Strategy

### AI Feature Tests

```python
# tests/test_ai_semantic_search.py
def test_semantic_search_finds_conceptual_matches():
    """Semantic search should find Thomas for 'doubt' query."""
    results = semantic_search.query("characters who doubted")
    char_ids = [r["id"] for r in results]
    assert "thomas" in char_ids

# tests/test_ai_contradiction_detection.py
def test_semantic_contradiction_detection():
    """Should identify genuine contradictions vs. complementary details."""
    analysis = semantic_contradictions.analyze_character_traits("jesus")
    # Verify structure and fields
    assert "semantic_analysis" in analysis
```

### Performance Benchmarks

- Embedding generation: < 100ms per character
- Semantic search: < 200ms for top-10 results
- Contradiction analysis: < 500ms per character

---

## Documentation Requirements

### User Documentation

- `docs/AI_FEATURES.md`: User guide for all AI features
- `docs/AI_CONFIGURATION.md`: Setup and configuration guide
- API reference additions to `docs/SCHEMA.md`

### Developer Documentation

- `docs/AI_ARCHITECTURE.md`: Technical design and implementation notes
- `docs/AI_MODEL_INTEGRATION.md`: Guide for adding new models
- Inline docstrings for all AI modules

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| **Accuracy**: AI generates incorrect analysis | Human review required for data updates; AI output clearly marked |
| **Complexity**: Too much AI complexity | Start with simple local models; advanced features optional |
| **Dependency creep**: Large model dependencies | Use lightweight models; support CPU-only inference |
| **Scope drift**: AI becomes a debate engine | Strict adherence to data-centric features; no theological argument generation |
| **Performance**: AI slows down core features | All AI features optional and async; never block core operations |

---

## Success Metrics

### Quantitative

- **Data quality**: 20% reduction in validation errors
- **Coverage**: 30% increase in trait completeness
- **Discovery**: 50+ new relationship suggestions reviewed
- **Performance**: AI features add < 5% overhead when disabled

### Qualitative

- **User feedback**: Positive reception from data entry contributors
- **External tool adoption**: At least 2 tools integrate AI-enhanced exports
- **Code quality**: All AI features maintain test coverage > 80%

---

## Open Questions

1. **Model hosting**: Should BCE include model weights in repo or download on first use?
2. **API key management**: Best practice for optional API-based features?
3. **Result versioning**: How to version AI-generated analyses as models improve?
4. **Community contributions**: Process for community-submitted AI feature ideas?

---

## Conclusion

These AI features enhance Codex Azazel's core mission as a data and analysis engine without compromising its focused scope. By prioritizing data quality, transparency, and tool-friendliness, we can leverage AI to improve the dataset while maintaining human oversight and scholarly rigor.

**Next Steps**:

1. Community feedback on this proposal
2. Prioritize features for Phase 6.1 implementation
3. Create detailed technical design documents for chosen features
4. Begin implementation with data quality features (highest ROI)

---

**Feedback welcome**: Please comment on specific features, raise concerns, or suggest alternatives.
