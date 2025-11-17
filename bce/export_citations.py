from __future__ import annotations

from typing import Any, Dict, Iterable, List

from . import sources, storage


def _escape_bibtex_value(value: str) -> str:
    """Very small helper to make strings safer for BibTeX fields.

    This is intentionally conservative; it only escapes braces and backslashes
    to avoid breaking the BibTeX syntax. Callers are expected to pass in
    already-normalized Unicode strings.
    """

    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _format_bibtex_entry(entry_type: str, key: str, fields: Dict[str, Any]) -> str:
    lines: List[str] = [f"@{entry_type}{{{key},"]
    for field_name, field_value in fields.items():
        if field_value is None:
            continue
        text = str(field_value)
        if not text.strip():
            continue
        escaped = _escape_bibtex_value(text)
        lines.append(f"  {field_name} = {{{escaped}}},")
    # Remove trailing comma on last field if present
    if len(lines) > 1 and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("}")
    return "\n".join(lines)


def _source_citations_bibtex() -> List[str]:
    entries: List[str] = []
    all_meta = sources.load_all_source_metadata()

    for source_id, meta in all_meta.items():
        key = f"source_{source_id}"
        title = source_id.replace("_", " ").title()
        note_parts: List[str] = []
        if meta.date_range:
            note_parts.append(f"date_range: {meta.date_range}")
        if meta.provenance:
            note_parts.append(f"provenance: {meta.provenance}")
        if meta.audience:
            note_parts.append(f"audience: {meta.audience}")
        if meta.depends_on:
            deps = ", ".join(meta.depends_on)
            note_parts.append(f"depends_on: {deps}")
        note = "; ".join(note_parts) if note_parts else None
        fields = {
            "title": title,
            "note": note,
            "keywords": f"bce-source,{source_id}",
        }
        entries.append(_format_bibtex_entry("misc", key, fields))

    return entries


def _character_citations_bibtex() -> List[str]:
    entries: List[str] = []

    for character in storage.iter_characters():
        key = f"character_{character.id}"
        sources_list = character.list_sources()
        fields = {
            "author": character.canonical_name,
            "title": f"Character profile: {character.canonical_name}",
            "note": f"Codex Azazel character id: {character.id}",
            "keywords": ",".join(["bce-character", character.id] + sources_list),
        }
        entries.append(_format_bibtex_entry("misc", key, fields))

    return entries


def _event_citations_bibtex() -> List[str]:
    entries: List[str] = []

    for event in storage.iter_events():
        key = f"event_{event.id}"
        source_ids = sorted({acc.source_id for acc in event.accounts})
        fields = {
            "title": f"Event: {event.label}",
            "note": f"Codex Azazel event id: {event.id}",
            "keywords": ",".join(["bce-event", event.id] + source_ids),
        }
        entries.append(_format_bibtex_entry("misc", key, fields))

    return entries


def export_citations(format: str = "bibtex") -> List[str]:
    """Export citations for BCE sources, characters, and events.

    Parameters
    ----------
    format:
        Citation format to use. Currently only ``"bibtex"`` is supported.

    Returns
    -------
    list of str
        A list of citation entries in the requested format. For BibTeX, each
        item is a complete ``@misc{...}`` record.
    """

    if format != "bibtex":
        raise ValueError(f"Unsupported citation format: {format!r}")

    entries: List[str] = []
    entries.extend(_source_citations_bibtex())
    entries.extend(_character_citations_bibtex())
    entries.extend(_event_citations_bibtex())
    return entries
