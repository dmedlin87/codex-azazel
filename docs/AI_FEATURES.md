# AI Features Documentation

**Status**: Implemented (Phases 6.1-6.3)
**Last Updated**: 2025-11-18

## Overview

Codex Azazel includes optional AI-powered features for data quality improvement, semantic search, and discovery. All AI features:

- **Are optional**: Disabled by default, require explicit enablement
- **Work offline-first**: Use local embeddings (no API calls required)
- **Are transparent**: All outputs include confidence scores and explanations
- **Respect boundaries**: No apologetics, debate logic, or theological arguments
- **Are data-centric**: Focus on improving data quality and discoverability

---

## Table of Contents

1. [Setup and Configuration](#setup-and-configuration)
2. [Data Quality Features](#data-quality-features)
   - [Semantic Contradiction Detection](#semantic-contradiction-detection)
   - [Completeness Auditing](#completeness-auditing)
   - [Validation Suggestions](#validation-suggestions)
3. [Enhanced Search](#enhanced-search)
   - [Semantic Search](#semantic-search)
   - [Finding Similar Characters](#finding-similar-characters)
   - [Thematic Clustering](#thematic-clustering)
4. [API Reference](#api-reference)
5. [Performance and Caching](#performance-and-caching)
6. [Troubleshooting](#troubleshooting)

---

## Setup and Configuration

### Installation

Install AI dependencies:

```bash
# Core AI features (local embeddings)
pip install 'codex-azazel[ai]'

# Optional: OpenAI support
pip install 'codex-azazel[ai-openai]'

# Optional: Anthropic support
pip install 'codex-azazel[ai-anthropic]'
```

### Enable AI Features

AI features must be explicitly enabled in configuration:

```python
from bce.config import BceConfig, set_default_config

# Enable AI features
config = BceConfig(enable_ai_features=True)
set_default_config(config)
```

Or via environment variable:

```bash
export BCE_ENABLE_AI_FEATURES=true
```

### Configuration Options

```python
from pathlib import Path
from bce.config import BceConfig, set_default_config

config = BceConfig(
    enable_ai_features=True,               # Enable AI features
    ai_model_backend="local",              # "local", "openai", or "anthropic"
    ai_cache_dir=Path("/custom/cache"),    # Custom cache directory
    embedding_model="all-MiniLM-L6-v2"     # Embedding model name
)

set_default_config(config)
```

Environment variables:

- `BCE_ENABLE_AI_FEATURES`: Enable/disable AI (default: false)
- `BCE_AI_MODEL_BACKEND`: Backend selection (default: local)
- `BCE_AI_CACHE_DIR`: Cache directory path
- `BCE_EMBEDDING_MODEL`: Model name (default: all-MiniLM-L6-v2)

---

## Data Quality Features

### Semantic Contradiction Detection

**Purpose**: Distinguish genuine contradictions from complementary details or different emphases.

**How it works**: Uses sentence embeddings to measure semantic similarity between conflicting trait values. Low similarity indicates genuine contradiction, high similarity indicates complementary details.

**Usage**:

```python
from bce import api

# Analyze character trait conflicts
analysis = api.analyze_semantic_contradictions("jesus")

print(f"Character: {analysis['canonical_name']}")
print(f"Has conflicts: {analysis['has_conflicts']}")
print(f"Genuine conflicts: {analysis['summary']['genuine_conflicts']}")
print(f"Complementary details: {analysis['summary']['complementary_details']}")

# Examine specific conflicts
for trait, details in analysis["analyzed_conflicts"].items():
    semantic = details["semantic_analysis"]
    print(f"\nTrait: {trait}")
    print(f"  Conflict type: {semantic['conflict_type']}")
    print(f"  Similarity: {semantic['similarity_score']}")
    print(f"  Severity: {semantic['severity']}")
    print(f"  Explanation: {semantic['explanation']}")
```

**Output structure**:

```python
{
    "character_id": "jesus",
    "canonical_name": "Jesus of Nazareth",
    "has_conflicts": True,
    "analyzed_conflicts": {
        "messianic_self_understanding": {
            "trait": "messianic_self_understanding",
            "sources": {
                "mark": "Avoids messianic titles publicly",
                "john": "Explicitly claims divinity"
            },
            "semantic_analysis": {
                "is_genuine_conflict": True,
                "conflict_type": "genuine_contradiction",
                "similarity_score": 0.23,
                "explanation": "...",
                "severity": "high"
            }
        }
    },
    "summary": {
        "total_conflicts": 5,
        "genuine_conflicts": 2,
        "complementary_details": 1,
        "different_emphases": 2
    }
}
```

**Conflict types**:

- `genuine_contradiction` (similarity < 0.5): Genuinely incompatible claims
- `different_emphasis` (similarity 0.5-0.8): Different perspectives/priorities
- `complementary_details` (similarity ≥ 0.8): Minor wording differences

### Completeness Auditing

**Purpose**: Identify gaps, missing data, and areas needing improvement.

**How it works**: Analyzes characters/events for missing source profiles, sparse traits, missing references/tags, and calculates completeness scores (0.0-1.0).

**Usage**:

```python
from bce import api

# Audit single character
audit = api.audit_character_completeness("thomas")

print(f"Completeness score: {audit['completeness_score']}")
print(f"Gaps found: {audit['gap_count']}")

# Examine gaps
for gap in audit["gaps"]:
    print(f"\n{gap['type']} ({gap['priority']})")
    print(f"  {gap['suggestion']}")

# Audit all characters
all_audits = api.audit_character_completeness(char_id=None)
print(f"Total characters: {all_audits['total_characters']}")
print(f"Average completeness: {all_audits['summary']['average_completeness']}")
print(f"Need attention: {all_audits['summary']['attention_count']}")
```

**Gap types**:

- `missing_source_profile`: Character may appear in source but lacks profile
- `sparse_traits`: Profile has < 2 traits
- `missing_references`: Profile lacks scripture references
- `missing_tags`: Character has no tags
- `missing_relationships`: Character has no documented relationships
- `tag_role_mismatch`: Roles don't align with tags

**Priority levels**:

- `critical`: No accounts (events only)
- `high`: Missing references
- `medium`: Missing source profiles, tags, single account
- `low`: Sparse traits, missing relationships

### Validation Suggestions

**Purpose**: AI-powered suggestions for fixing validation errors.

**How it works**: Analyzes validation error patterns and suggests fixes using string similarity and pattern matching.

**Usage**:

```python
from bce import api

# Get suggestions for current validation errors
suggestions = api.get_validation_suggestions()

for sugg in suggestions:
    print(f"Error: {sugg['error']}")
    print(f"Suggestion: {sugg['suggestion']}")
    print(f"Confidence: {sugg['confidence']:.2f}")
    if sugg['similar_items']:
        print(f"Similar items: {sugg['similar_items']}")
    print()

# Pass specific errors
errors = ["Character 'foo' references unknown event 'bar_event'"]
suggestions = api.get_validation_suggestions(errors)
```

**Handled error types**:

- Missing character/event references → Suggests similar IDs
- Invalid scripture references → Provides format guidance
- Missing required fields → Points to schema docs
- JSON syntax errors → Identifies common issues

---

## Enhanced Search

### Semantic Search

**Purpose**: Search by concept rather than exact keywords.

**How it works**: Embeds search query and all searchable content, then returns results ranked by cosine similarity.

**Usage**:

```python
from bce import api

# Conceptual search
results = api.semantic_search("characters who doubted but came to believe")

for result in results[:5]:
    print(f"{result['id']}: {result['relevance_score']:.2f}")
    print(f"  Matched in: {result['match_in']}")
    print(f"  Context: {result['matching_context'][:100]}...")
    print(f"  Explanation: {result['explanation']}")
    print()

# Scoped search
trait_results = api.semantic_search(
    "suffering and persecution",
    scope=["traits"],
    top_k=5,
    min_score=0.4
)
```

**Scope options**:

- `traits`: Character traits
- `relationships`: Character relationships
- `accounts`: Event accounts

**Output**:

```python
{
    "type": "character",
    "id": "thomas",
    "relevance_score": 0.89,
    "matching_context": "doubt_and_belief: Refuses to believe without physical proof...",
    "match_in": "traits.john.doubt_and_belief",
    "explanation": "Strong semantic match: Query 'characters who doubted' is conceptually similar to content in character 'thomas'"
}
```

### Finding Similar Characters

**Purpose**: Find characters with similar traits, roles, or themes.

**How it works**: Compares character embeddings to find conceptual similarity.

**Usage**:

```python
from bce import api

# Find similar characters
similar = api.find_similar_characters("paul", top_k=5)

for char in similar:
    print(f"{char['canonical_name']}: {char['similarity_score']:.2f}")

# Use specific fields for comparison
similar = api.find_similar_characters(
    "peter",
    top_k=3,
    basis=["traits", "roles"]
)
```

**Basis options**:

- `traits`: Character traits (default)
- `roles`: Character roles
- `tags`: Character tags
- `relationships`: Relationship descriptions

### Thematic Clustering

**Purpose**: Automatically discover thematic groupings.

**How it works**: Uses K-means clustering on character/event embeddings to identify natural groupings.

**Usage**:

```python
from bce import api

# Discover character clusters
clusters = api.find_thematic_clusters(num_clusters=6)

for cluster in clusters:
    print(f"\n{cluster['label']}")
    print(f"  Confidence: {cluster['confidence']:.2f}")
    print(f"  Size: {cluster['size']}")
    print(f"  Members: {cluster['members']}")
    print(f"  Representative traits: {cluster['representative_traits']}")

# Event clustering
event_clusters = api.find_thematic_clusters(
    entity_type="events",
    num_clusters=4
)

# Get tag suggestions from clusters
from bce.ai import clustering
suggestions = clustering.suggest_tags_from_clusters(clusters)
print(f"Suggested tags for paul: {suggestions['paul']}")
```

**Cluster output**:

```python
{
    "cluster_id": "cluster_0",
    "label": "Apostolic Leaders",
    "members": ["peter", "john", "james_son_of_zebedee"],
    "member_names": ["Peter (Simon)", "John", "James (son of Zebedee)"],
    "representative_traits": ["apostle", "disciple", "fisherman"],
    "confidence": 0.87,
    "size": 3
}
```

---

## API Reference

All AI features are exposed via `bce.api`:

### Data Quality

```python
from bce import api

# Semantic contradiction analysis
analysis = api.analyze_semantic_contradictions(char_id, use_cache=True)

# Completeness auditing
audit = api.audit_character_completeness(char_id=None, use_cache=True)

# Validation suggestions
suggestions = api.get_validation_suggestions(errors=None, use_cache=True)
```

### Enhanced Search

```python
from bce import api

# Semantic search
results = api.semantic_search(
    query,
    top_k=10,
    scope=None,  # ["traits", "relationships", "accounts"]
    min_score=0.3,
    use_cache=True
)

# Find similar characters
similar = api.find_similar_characters(
    char_id,
    top_k=5,
    basis=None  # ["traits", "roles", "tags", "relationships"]
)

# Thematic clustering
clusters = api.find_thematic_clusters(
    entity_type="characters",  # or "events"
    num_clusters=8,
    basis=None,  # ["traits", "tags", "roles"] for characters
    use_cache=True
)
```

All functions raise:
- `ConfigurationError` if AI features are disabled
- `ImportError` if required dependencies are missing

---

## Performance and Caching

### Cache Strategy

- **Embeddings**: Permanently cached until data changes
- **Search index**: 1 hour TTL (auto-refreshes)
- **Analysis results**: 24 hour TTL
- **Clustering**: 2 hour TTL

### Cache Management

```python
from bce.ai.cache import clear_all_ai_caches

# Clear all AI caches
clear_all_ai_caches()

# Character-specific cache invalidation
from bce.ai.cache import invalidate_character_caches
invalidate_character_caches("paul")

# Event-specific cache invalidation
from bce.ai.cache import invalidate_event_caches
invalidate_event_caches("crucifixion")
```

### Performance Benchmarks

With local embeddings (all-MiniLM-L6-v2):

- **Embedding generation**: 50-100ms per item
- **Semantic search**: 50-200ms (cached index)
- **Similarity calculation**: 10-50ms
- **Clustering**: 500ms-2s depending on dataset size
- **Contradiction analysis**: 200-500ms per character

### Storage Requirements

- **Embedding model**: ~80MB (downloaded on first use)
- **Embedding cache**: ~1-5MB per 100 cached items
- **Analysis cache**: ~10-100KB per cached result

---

## Troubleshooting

### AI Features Not Enabled

**Error**: `ConfigurationError: AI features are disabled`

**Solution**:

```python
from bce.config import BceConfig, set_default_config

config = BceConfig(enable_ai_features=True)
set_default_config(config)
```

### Missing Dependencies

**Error**: `ImportError: sentence-transformers is required`

**Solution**:

```bash
pip install 'codex-azazel[ai]'
```

### Slow First Run

AI features download the embedding model on first use (~80MB). Subsequent runs use cached model.

**Speed up**:

```bash
# Pre-download model
python -c "from bce.ai.embeddings import _get_model; _get_model()"
```

### Cache Location

Default cache location: `{data_root}/ai_cache`

Custom location:

```python
from pathlib import Path
from bce.config import BceConfig, set_default_config

config = BceConfig(
    enable_ai_features=True,
    ai_cache_dir=Path("/custom/cache")
)
set_default_config(config)
```

### Memory Usage

Embedding model uses ~500MB RAM during operation. For memory-constrained environments:

```python
# Use smaller embedding model
config = BceConfig(
    enable_ai_features=True,
    embedding_model="paraphrase-MiniLM-L3-v2"  # Smaller, faster, slightly lower quality
)
```

### Clear Corrupted Cache

```python
from bce.ai.cache import clear_all_ai_caches

clear_all_ai_caches()
```

---

## Examples

### Complete Workflow: Data Quality Audit

```python
from bce import api
from bce.config import BceConfig, set_default_config

# Enable AI
config = BceConfig(enable_ai_features=True)
set_default_config(config)

# 1. Check for validation errors and get suggestions
suggestions = api.get_validation_suggestions()
print(f"Found {len(suggestions)} validation issues")

# 2. Audit all characters for completeness
audits = api.audit_character_completeness()
low_completeness = [
    char_id for char_id, audit in audits["results"].items()
    if audit["completeness_score"] < 0.70
]
print(f"{len(low_completeness)} characters need attention")

# 3. Analyze contradictions for key characters
for char_id in ["jesus", "paul", "peter"]:
    analysis = api.analyze_semantic_contradictions(char_id)
    genuine = analysis["summary"]["genuine_conflicts"]
    if genuine > 0:
        print(f"{char_id}: {genuine} genuine conflicts")
```

### Complete Workflow: Discovery and Exploration

```python
from bce import api

# 1. Semantic search for themes
results = api.semantic_search("transformation and redemption")
print(f"Found {len(results)} related characters/events")

# 2. Find thematic clusters
clusters = api.find_thematic_clusters(num_clusters=5)
for cluster in clusters:
    print(f"{cluster['label']}: {len(cluster['members'])} members")

# 3. Explore similar characters
similar = api.find_similar_characters("paul", top_k=3)
for char in similar:
    print(f"Similar to Paul: {char['canonical_name']} ({char['similarity_score']:.2f})")
```

---

## Frequently Asked Questions

### Q: Do I need internet access?

A: No. AI features work completely offline using local embeddings. Internet is only needed for initial model download.

### Q: Are my queries sent to external services?

A: No. By default, all processing happens locally. External API backends (OpenAI, Anthropic) are opt-in only.

### Q: How accurate is semantic contradiction detection?

A: Semantic similarity provides a heuristic, not a definitive theological judgment. Treat results as suggestions requiring human review.

### Q: Can I use custom embedding models?

A: Yes. Set `embedding_model` in BceConfig to any sentence-transformers model name.

### Q: How do I disable caching for testing?

A: Pass `use_cache=False` to any AI function.

### Q: Does this add theological interpretations?

A: No. AI features analyze data structure and semantics, not theology. No apologetics or debate logic is included.

---

## See Also

- [AI Features Proposal](./AI_FEATURES_PROPOSAL.md) - Full technical specification
- [AI Features Quick Reference](./AI_FEATURES_QUICK_REF.md) - Quick feature summary
- [SCHEMA.md](./SCHEMA.md) - API schema documentation
- [ROADMAP.md](./ROADMAP.md) - Project roadmap
- [CLAUDE.md](../CLAUDE.md) - AI assistant development guide
