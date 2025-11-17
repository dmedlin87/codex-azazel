from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

from . import storage


def _export_csv(rows: Iterable[Mapping[str, str]], output_path: str, fieldnames: list[str]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def export_characters_csv(output_path: str, include_fields: Iterable[str] | None = None) -> None:
    default_fields = ["id", "canonical_name", "aliases", "roles", "source_count"]
    fieldnames = list(include_fields) if include_fields is not None else default_fields
    rows = []
    for character in storage.iter_characters():
        sources = character.list_sources()
        row = {
            "id": character.id,
            "canonical_name": character.canonical_name,
            "name": character.canonical_name,
            "aliases": ", ".join(character.aliases),
            "roles": ", ".join(character.roles),
            "source_count": str(len(sources)),
            "sources": ", ".join(sources),
        }
        rows.append(row)
    _export_csv(rows, output_path, fieldnames)


def export_events_csv(output_path: str, include_fields: Iterable[str] | None = None) -> None:
    default_fields = [
        "id",
        "label",
        "participants",
        "participant_count",
        "account_count",
        "sources",
        "source_count",
    ]
    fieldnames = list(include_fields) if include_fields is not None else default_fields
    rows = []
    for event in storage.iter_events():
        source_ids = sorted({acc.source_id for acc in event.accounts})
        row = {
            "id": event.id,
            "label": event.label,
            "participants": ", ".join(event.participants),
            "participant_count": str(len(event.participants)),
            "account_count": str(len(event.accounts)),
            "sources": ", ".join(source_ids),
            "source_count": str(len(source_ids)),
        }
        rows.append(row)
    _export_csv(rows, output_path, fieldnames)
