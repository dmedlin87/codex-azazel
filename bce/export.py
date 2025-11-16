from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from . import storage


def _export_iterable(objs: Iterable[object], output_path: str) -> None:
    """Export an iterable of dataclass instances to a JSON file.

    The resulting file contains a JSON list of plain dictionaries.
    """
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


def dossier_to_markdown(dossier: dict) -> str:
    """Render a single dossier dictionary as a Markdown string.

    This function assumes it receives the JSON-friendly structures
    produced by helpers in :mod:`bce.dossiers`. It is intentionally
    tolerant of missing optional fields and will simply omit any
    sections it cannot recognize.
    """

    lines: list[str] = []

    # Title / primary label
    title_key_candidates = ["canonical_name", "label", "title", "name", "id"]
    title_value = None
    for key in title_key_candidates:
        if key in dossier and isinstance(dossier[key], str) and dossier[key]:
            title_value = dossier[key]
            break

    if title_value is None:
        title_value = "<unknown>"

    lines.append(f"# {title_value}")

    # Canonical ID line
    dossier_id = dossier.get("id")
    if isinstance(dossier_id, str) and dossier_id:
        lines.append(f"ID: {dossier_id}")

    # Optional summary / description paragraph
    for summary_key in ("summary", "description"):
        summary = dossier.get(summary_key)
        if isinstance(summary, str) and summary.strip():
            lines.append("")
            lines.append(summary.strip())
            break

    # Helper to add a list-based section.
    def _add_list_section(title: str, values: Iterable[str]) -> None:
        values = [v for v in values if isinstance(v, str) and v.strip()]
        if not values:
            return
        lines.append("")
        lines.append(f"## {title}")
        for value in values:
            lines.append(f"- {value.strip()}")

    # Helper to add a mapping section where values are simple strings.
    def _add_simple_mapping_section(title: str, mapping: dict) -> None:
        if not isinstance(mapping, dict) or not mapping:
            return
        lines.append("")
        lines.append(f"## {title}")
        for key, value in mapping.items():
            if not isinstance(key, str):
                continue
            if not isinstance(value, str):
                continue
            if not value.strip():
                continue
            lines.append(f"- {key}: {value.strip()}")

    # Helper to render nested mapping sections (e.g. comparisons/conflicts).
    def _add_nested_mapping_section(title: str, mapping: dict) -> None:
        if not isinstance(mapping, dict) or not mapping:
            return
        lines.append("")
        lines.append(f"## {title}")
        for key, value in mapping.items():
            if not isinstance(key, str):
                continue
            if isinstance(value, dict):
                # Summarize nested dict as k=v pairs.
                parts = []
                for sub_key, sub_val in value.items():
                    parts.append(f"{sub_key}={sub_val}")
                summary = ", ".join(parts)
                lines.append(f"- {key}: {summary}")
            else:
                lines.append(f"- {key}: {value}")

    # Character-oriented sections
    aliases = dossier.get("aliases")
    if isinstance(aliases, list):
        _add_list_section("Aliases", aliases)

    roles = dossier.get("roles")
    if isinstance(roles, list):
        _add_list_section("Roles", roles)

    source_ids = dossier.get("source_ids")
    if isinstance(source_ids, list):
        _add_list_section("Source IDs", source_ids)

    traits_by_source = dossier.get("traits_by_source")
    if isinstance(traits_by_source, dict):
        lines.append("")
        lines.append("## Traits by source")
        for source_id, traits in traits_by_source.items():
            if not isinstance(source_id, str) or not isinstance(traits, dict):
                continue
            parts = []
            for trait_name, trait_value in traits.items():
                parts.append(f"{trait_name}={trait_value}")
            summary = ", ".join(parts)
            lines.append(f"- {source_id}: {summary}")

    references_by_source = dossier.get("references_by_source")
    if isinstance(references_by_source, dict):
        lines.append("")
        lines.append("## References by source")
        for source_id, refs in references_by_source.items():
            if not isinstance(source_id, str) or not isinstance(refs, list):
                continue
            cleaned_refs = [r for r in refs if isinstance(r, str) and r.strip()]
            if not cleaned_refs:
                continue
            lines.append(f"- {source_id}:")
            for ref in cleaned_refs:
                lines.append(f"  - {ref.strip()}")

    trait_comparison = dossier.get("trait_comparison")
    if isinstance(trait_comparison, dict):
        _add_nested_mapping_section("Trait comparison", trait_comparison)

    trait_conflicts = dossier.get("trait_conflicts")
    if isinstance(trait_conflicts, dict):
        _add_nested_mapping_section("Trait conflicts", trait_conflicts)

    # Event-oriented sections
    participants = dossier.get("participants")
    if isinstance(participants, list):
        _add_list_section("Participants", participants)

    accounts = dossier.get("accounts")
    if isinstance(accounts, list) and accounts:
        lines.append("")
        lines.append("## Accounts")
        for acc in accounts:
            if not isinstance(acc, dict):
                continue
            # Promote a few important keys if present.
            source = acc.get("source_id")
            reference = acc.get("reference")
            summary = acc.get("summary")
            bullet_parts = []
            if source:
                bullet_parts.append(f"source={source}")
            if reference:
                bullet_parts.append(f"ref={reference}")
            if summary:
                bullet_parts.append(f"summary={summary}")
            if not bullet_parts:
                # Fallback: compact representation of the dict.
                bullet_parts = [f"{k}={v}" for k, v in acc.items()]
            lines.append(f"- {'; '.join(bullet_parts)}")

    account_conflicts = dossier.get("account_conflicts")
    if isinstance(account_conflicts, dict):
        _add_nested_mapping_section("Account conflicts", account_conflicts)

    return "\n".join(lines)


def dossiers_to_markdown(dossiers: dict[str, dict]) -> str:
    """Render a mapping of IDs to dossiers as a single Markdown string.

    Each dossier is separated by a horizontal rule style delimiter so that
    individual blocks remain visually distinct.
    """

    blocks: list[str] = []
    for dossier in dossiers.values():
        # Be tolerant of non-dict values; skip anything unexpected.
        if not isinstance(dossier, dict):
            continue
        blocks.append(dossier_to_markdown(dossier))

    return "\n\n---\n\n".join(blocks)
