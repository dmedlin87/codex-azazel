from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from . import storage


def _export_iterable(objs: Iterable[object], output_path: str) -> None:
    """Export an iterable of dataclass instances to a JSON file."""
    path = Path(output_path)
    data = [asdict(obj) for obj in objs]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_all_characters(output_path: str) -> None:
    """Export all characters to a single JSON file at ``output_path``."""
    _export_iterable(storage.iter_characters(), output_path)


def export_all_events(output_path: str) -> None:
    """Export all events to a single JSON file at ``output_path``."""
    _export_iterable(storage.iter_events(), output_path)
