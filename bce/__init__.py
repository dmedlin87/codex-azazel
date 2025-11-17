"""Codex Azazel - Biblical Character Engine (BCE).

A contradiction-aware Biblical character and event engine focused on
New Testament data analysis.

Public API:
    - Core models: Character, Event, SourceProfile, EventAccount
    - Data access: api module for high-level operations
    - Exceptions: BceError and subclasses
    - Configuration: BceConfig for customization

Example:
    >>> import bce
    >>> # Get a character
    >>> jesus = bce.api.get_character("jesus")
    >>> # Build a dossier
    >>> dossier = bce.api.build_character_dossier("jesus")
    >>> # Find conflicts
    >>> conflicts = bce.api.summarize_character_conflicts("jesus")
"""

from __future__ import annotations

# Core data models
from .models import Character, SourceProfile, Event, EventAccount, SourceMetadata

# Configuration and infrastructure
from .config import BceConfig
from .cache import CacheRegistry
from .storage import StorageManager

# Exceptions
from .exceptions import (
    BceError,
    DataNotFoundError,
    ValidationError,
    StorageError,
    CacheError,
    ConfigurationError,
    SearchError,
)

# Public API modules
from . import api
from . import queries

# Version
__version__ = "0.1.0"

# Public exports
__all__ = [
    # Data models
    "Character",
    "SourceProfile",
    "Event",
    "EventAccount",
    "SourceMetadata",
    # Configuration
    "BceConfig",
    "StorageManager",
    "CacheRegistry",
    # Exceptions
    "BceError",
    "DataNotFoundError",
    "ValidationError",
    "StorageError",
    "CacheError",
    "ConfigurationError",
    "SearchError",
    # API modules
    "api",
    "queries",
    # Metadata
    "__version__",
]
