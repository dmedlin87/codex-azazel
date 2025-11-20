"""
AI-powered features for Codex Azazel.

This module provides optional AI enhancements for:
- Data quality improvement
- Enhanced search and discovery
- Data extraction assistance
- Advanced analytics

All AI features are:
- Optional (require explicit enablement)
- Transparent (outputs clearly marked)
- Data-centric (no apologetics or debate logic)
- Privacy-respecting (offline-first by default)
"""

from __future__ import annotations

# Import submodules for easier access
from . import cache, config, embeddings, models
# Phase 6.2: Data Quality Features
from . import completeness, semantic_contradictions, validation_assistant
# Phase 6.3: Enhanced Search
from . import clustering, semantic_search, question_answering
# Phase 6.4: Data Extraction Tools
from . import trait_extraction, parallel_detection, relationship_inference
# Phase 6.5: Export & Analytics
from . import summaries, source_analysis, conflict_analysis, event_reconstruction
# Phase 7: Advanced Features
from . import virtual_sources, trajectory, corpus_ingestion

__all__ = [
    # Foundation (Phase 6.1)
    "config",
    "embeddings",
    "cache",
    "models",
    # Data Quality (Phase 6.2)
    "completeness",
    "semantic_contradictions",
    "validation_assistant",
    # Enhanced Search (Phase 6.3)
    "semantic_search",
    "clustering",
    "question_answering",
    # Data Extraction (Phase 6.4)
    "trait_extraction",
    "parallel_detection",
    "relationship_inference",
    # Export & Analytics (Phase 6.5)
    "summaries",
    "source_analysis",
    "conflict_analysis",
    "event_reconstruction",
    # Advanced Features (Phase 7)
    "virtual_sources",
    "trajectory",
    "corpus_ingestion",
]
