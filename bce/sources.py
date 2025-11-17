from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import SourceMetadata


_PACKAGE_DIR = Path(__file__).resolve().parent
_SOURCES_PATH = _PACKAGE_DIR / "data" / "sources.json"


def _read_sources_raw() -> Dict[str, Any]:
    if not _SOURCES_PATH.exists():
        return {}
    with _SOURCES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_source_ids() -> List[str]:
    data = _read_sources_raw()
    return sorted(k for k in data.keys() if isinstance(k, str))


def load_source_metadata(source_id: str) -> Optional[SourceMetadata]:
    data = _read_sources_raw()
    raw = data.get(source_id)
    if not isinstance(raw, dict):
        return None

    depends_on_raw = raw.get("depends_on", [])
    if not isinstance(depends_on_raw, list):
        depends_on: List[str] = []
    else:
        depends_on = [str(item) for item in depends_on_raw]

    return SourceMetadata(
        source_id=source_id,
        date_range=raw.get("date_range"),
        provenance=raw.get("provenance"),
        audience=raw.get("audience"),
        depends_on=depends_on,
    )


def load_all_source_metadata() -> Dict[str, SourceMetadata]:
    results: Dict[str, SourceMetadata] = {}
    for source_id in list_source_ids():
        meta = load_source_metadata(source_id)
        if meta is not None:
            results[source_id] = meta
    return results
