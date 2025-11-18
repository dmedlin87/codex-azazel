# AI Features Quick Reference

**Full Proposal**: See [AI_FEATURES_PROPOSAL.md](./AI_FEATURES_PROPOSAL.md)

## Feature Summary

### 🔍 Data Quality (Phase 6.2)

| Feature | Purpose | Priority |
|---------|---------|----------|
| Semantic Contradiction Detection | Detect conflicts beyond string matching | HIGH |
| Data Completeness Auditor | Identify gaps and inconsistencies | HIGH |
| Smart Validation Suggestions | AI-powered fix suggestions for errors | MEDIUM |

### 🔎 Enhanced Search (Phase 6.3)

| Feature | Purpose | Priority |
|---------|---------|----------|
| Semantic Search | Concept-based search vs keyword matching | HIGH |
| Thematic Clustering | Auto-discover character/event groupings | MEDIUM |
| Question Answering | Natural language queries over data | LOW |

### 📝 Data Entry Assistance (Phase 6.4)

| Feature | Purpose | Priority |
|---------|---------|----------|
| Automated Trait Extraction | Extract traits from scripture text | HIGH |
| Parallel Passage Detection | Auto-identify synoptic parallels | MEDIUM |
| Relationship Inference | Suggest character relationships | MEDIUM |

### 📊 Export & Analytics (Phase 6.5)

| Feature | Purpose | Priority |
|---------|---------|----------|
| Natural Language Summaries | Generate readable dossier summaries | MEDIUM |
| Enhanced Citations | Auto-generate academic citations | LOW |
| Source Tendency Analysis | Identify systematic source patterns | MEDIUM |
| Advanced Conflict Analysis | Deep assessment of contradiction significance | MEDIUM |
| Event Reconstruction | Synthesize multi-source timelines | LOW |

## Implementation Status

1. **Phase 6.1 - Foundation** ✅ COMPLETE
   - Set up `bce/ai/` module structure
   - Implement local embedding support
   - Add AI feature configuration

2. **Phase 6.2 - Data Quality** ✅ COMPLETE
   - Semantic contradiction detection
   - Completeness auditor
   - Validation suggestions

3. **Phase 6.3 - Enhanced Search** ✅ COMPLETE
   - Semantic search with embeddings
   - Character clustering
   - Question answering

4. **Phase 6.4 - Data Entry Tools** ✅ COMPLETE
   - Trait extraction
   - Parallel detection
   - Relationship inference

5. **Phase 6.5 - Analytics** ✅ COMPLETE
   - Natural language summaries
   - Source tendency analysis
   - Advanced conflict analysis
   - Event reconstruction

**Status**: All phases (6.1-6.5) fully implemented!

## Quick Start for Contributors

### Using AI Features (once implemented)

```python
from bce import api
from bce.ai import semantic_search, completeness

# Enable AI features in config
from bce.config import BceConfig, set_default_config
config = BceConfig(enable_ai_features=True)
set_default_config(config)

# Semantic search
results = semantic_search.query("doubting disciples")

# Check data quality
audit = completeness.audit_characters()
```

### Configuration Options

```python
# Local models only (no API calls)
config = BceConfig(
    enable_ai_features=True,
    ai_model_backend="local",
    embedding_model="all-MiniLM-L6-v2"
)

# Use OpenAI for advanced features
config = BceConfig(
    enable_ai_features=True,
    ai_model_backend="openai",
    openai_api_key="sk-..."
)
```

## Model Requirements

### Local/Offline (Recommended)

- **Storage**: ~100MB for embeddings model
- **RAM**: ~500MB during indexing
- **CPU**: Any modern CPU (no GPU required)
- **Performance**: 50-200ms per query

### API-Based (Optional)

- **OpenAI**: Requires API key and internet connection
- **Anthropic**: Requires API key and internet connection
- **Cost**: Pay-per-use (varies by feature)

## Key Design Principles

1. **Offline-First**: All core features work without internet
2. **Optional**: AI features never block core functionality
3. **Transparent**: AI outputs clearly marked and explainable
4. **Human-in-the-Loop**: Critical updates require approval
5. **Data-Centric**: Focus on data quality, not debate or apologetics

## Example Use Cases

### Use Case 1: Data Entry Acceleration

```bash
# Extract traits from a passage
bce ai extract-traits \
  --character nicodemus \
  --source john \
  --reference "John 3:1-21" \
  --review

# Review suggestions, approve/edit, auto-add to JSON
```

### Use Case 2: Quality Audit

```python
from bce.ai import completeness

# Audit all characters for gaps
report = completeness.audit_characters()

# Get prioritized list of data entry tasks
for char_id, audit in report.items():
    if audit["completeness_score"] < 0.7:
        print(f"{char_id}: {audit['gaps']}")
```

### Use Case 3: Discover Hidden Patterns

```python
from bce.ai import clustering

# Find thematic clusters
clusters = clustering.find_character_clusters(num_clusters=8)

# Use for tag suggestions
for cluster in clusters:
    print(f"{cluster['label']}: {cluster['members']}")
```

### Use Case 4: Enhanced Search for External Tools

```python
from bce.ai import semantic_search

# Tool queries BCE for conceptual matches
results = semantic_search.query(
    "characters who experience transformation",
    top_k=5
)

# Export results with explanations
for result in results:
    print(f"{result['id']}: {result['explanation']}")
```

## Testing AI Features

```bash
# Run AI feature tests
pytest tests/test_ai_*.py

# Test with local models only
pytest tests/test_ai_*.py --local-only

# Benchmark performance
pytest tests/test_ai_performance.py --benchmark
```

## Feedback & Contribution

- **Questions**: Open an issue with `[AI Features]` prefix
- **Feature Requests**: Comment on AI_FEATURES_PROPOSAL.md
- **Implementation PRs**: Reference proposal section in PR description

## Related Documentation

- [Full Proposal](./AI_FEATURES_PROPOSAL.md) - Complete technical specification
- [ROADMAP.md](./ROADMAP.md) - Project roadmap (Phases 0-5 complete)
- [SCHEMA.md](./SCHEMA.md) - API schema documentation
- [CLAUDE.md](../CLAUDE.md) - AI assistant guide for development

---

**Status**: **IMPLEMENTED** (Phases 6.1-6.5 Complete)
**Last Updated**: 2025-11-18
