from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class ChangeRecord:
    timestamp: str  # ISO format
    entity_type: str  # "character" or "event"
    entity_id: str
    change_type: str  # "create", "update", "delete"
    field_changes: Dict[str, Dict[str, Any]]  # {"field": {"old": ..., "new": ...}}
    author: Optional[str] = None
    message: Optional[str] = None

class ChangeLog:
    """Track data changes over time using a JSON-based log."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self._changes: List[ChangeRecord] = []
        self._load()

    def _load(self) -> None:
        """Load changelog from file."""
        if self.log_file.exists():
            try:
                with self.log_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._changes = [
                        ChangeRecord(**record) for record in data
                    ]
            except Exception as e:
                logger.error(f"Failed to load changelog from {self.log_file}: {e}")
                # Start with empty if corrupted or unreadable
                self._changes = []

    def _save(self) -> None:
        """Save changelog to file."""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file.open("w", encoding="utf-8") as f:
                json.dump(
                    [asdict(c) for c in self._changes],
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            logger.error(f"Failed to save changelog to {self.log_file}: {e}")

    def record_change(self, record: ChangeRecord) -> None:
        """Record a change and save to disk."""
        self._changes.append(record)
        self._save()

    def get_history(self, entity_id: str) -> List[ChangeRecord]:
        """Get full history for an entity."""
        return [c for c in self._changes if c.entity_id == entity_id]

    def get_recent_changes(self, limit: int = 10) -> List[ChangeRecord]:
        """Get most recent changes."""
        return sorted(self._changes, key=lambda c: c.timestamp, reverse=True)[:limit]
