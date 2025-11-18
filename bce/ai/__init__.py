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

__all__ = [
    "config",
    "embeddings",
    "cache",
    "models",
]
