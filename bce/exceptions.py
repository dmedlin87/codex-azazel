from __future__ import annotations


class BceError(Exception):
    """Base exception for all BCE (Biblical Character Engine) errors.

    All custom exceptions in the BCE package inherit from this base class,
    making it easy to catch any BCE-specific error.
    """


class DataNotFoundError(FileNotFoundError, BceError):
    """Raised when requested character, event, or source data doesn't exist.

    Examples:
        - Loading a character ID that doesn't have a corresponding JSON file
        - Requesting an event that hasn't been defined
        - Accessing a source that isn't in the sources registry
    """


class ValidationError(BceError):
    """Raised when data validation fails.

    Examples:
        - Invalid scripture references
        - Character ID mismatch between filename and JSON content
        - Event participants referencing non-existent characters
        - Duplicate IDs in the dataset
    """


class StorageError(RuntimeError, BceError):
    """Raised when storage operations fail.

    Examples:
        - File I/O errors during load/save operations
        - JSON parsing errors
        - Permission issues accessing data directories
        - Invalid data root configuration
    """


class CacheError(BceError):
    """Raised when cache operations fail.

    Examples:
        - Cache invalidation failures
        - Cache registry errors
    """


class ConfigurationError(BceError):
    """Raised when configuration is invalid or missing.

    Examples:
        - Invalid environment variable values
        - Missing required configuration
        - Conflicting configuration settings
    """


class SearchError(BceError):
    """Raised when search operations fail.

    Examples:
        - Invalid search scope
        - Malformed search queries
    """
