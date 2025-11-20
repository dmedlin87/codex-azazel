"""Schema gate between raw JSON and BCE models.

This keeps the core light (stdlib only) while enforcing a strict shape for
character and event payloads before they are turned into dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import ValidationError


@dataclass
class SchemaContext:
    """Context for validation error messages."""

    path: Optional[Path] = None
    entity_id: Optional[str] = None

    def prefix(self) -> str:
        pieces = []
        if self.path:
            pieces.append(str(self.path))
        if self.entity_id:
            pieces.append(self.entity_id)
        return " ".join(pieces).strip() or "payload"


def _expect_str(value: Any, field: str, errors: List[str], ctx: SchemaContext) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{ctx.prefix()}: field '{field}' must be a non-empty string")
        return False
    return True


def _expect_list(value: Any, field: str, errors: List[str], ctx: SchemaContext) -> Optional[list]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    errors.append(f"{ctx.prefix()}: field '{field}' must be a list")
    return None


def validate_character_raw(data: Dict[str, Any], *, path: Optional[Path] = None) -> None:
    """Validate raw character JSON structure.

    Raises ValidationError on any structural issue.
    """
    errors: List[str] = []
    ctx = SchemaContext(path=path, entity_id=data.get("id"))

    _expect_str(data.get("id"), "id", errors, ctx)
    _expect_str(data.get("canonical_name"), "canonical_name", errors, ctx)

    profiles = _expect_list(data.get("source_profiles"), "source_profiles", errors, ctx)
    if profiles is not None:
        for idx, profile in enumerate(profiles):
            if not isinstance(profile, dict):
                errors.append(f"{ctx.prefix()}: source_profiles[{idx}] must be an object")
                continue
            if not _expect_str(profile.get("source_id"), f"source_profiles[{idx}].source_id", errors, ctx):
                continue

            traits = profile.get("traits") or profile.get("trait_notes") or {}
            if traits is not None and not isinstance(traits, dict):
                errors.append(
                    f"{ctx.prefix()}: source_profiles[{idx}].traits must be an object of key/value pairs"
                )

            structured = profile.get("structured_traits")
            if structured is not None and not isinstance(structured, dict):
                errors.append(
                    f"{ctx.prefix()}: source_profiles[{idx}].structured_traits must be an object"
                )

            refs = profile.get("references")
            if refs is not None and not isinstance(refs, list):
                errors.append(
                    f"{ctx.prefix()}: source_profiles[{idx}].references must be a list of strings"
                )

    relationships = data.get("relationships")
    if relationships is not None:
        rels = _expect_list(relationships, "relationships", errors, ctx)
        if rels is not None:
            for ridx, rel in enumerate(rels):
                if not isinstance(rel, dict):
                    errors.append(f"{ctx.prefix()}: relationships[{ridx}] must be an object")
                    continue
                if not (
                    _expect_str(
                        rel.get("target_id") or rel.get("character_id") or rel.get("to"),
                        f"relationships[{ridx}].target_id",
                        errors,
                        ctx,
                    )
                ):
                    continue
                _expect_str(
                    rel.get("type") or rel.get("relationship_type"),
                    f"relationships[{ridx}].type",
                    errors,
                    ctx,
                )

    if errors:
        raise ValidationError("; ".join(errors))


def validate_event_raw(data: Dict[str, Any], *, path: Optional[Path] = None) -> None:
    """Validate raw event JSON structure."""
    errors: List[str] = []
    ctx = SchemaContext(path=path, entity_id=data.get("id"))

    _expect_str(data.get("id"), "id", errors, ctx)
    _expect_str(data.get("label"), "label", errors, ctx)

    accounts = _expect_list(data.get("accounts"), "accounts", errors, ctx)
    if accounts is not None:
        for idx, account in enumerate(accounts):
            if not isinstance(account, dict):
                errors.append(f"{ctx.prefix()}: accounts[{idx}] must be an object")
                continue
            _expect_str(account.get("source_id"), f"accounts[{idx}].source_id", errors, ctx)
            _expect_str(account.get("reference"), f"accounts[{idx}].reference", errors, ctx)
            # summary can be optional, but when present must be a string
            summary = account.get("summary")
            if summary is not None and not isinstance(summary, str):
                errors.append(f"{ctx.prefix()}: accounts[{idx}].summary must be a string")

    participants = data.get("participants")
    if participants is not None and not isinstance(participants, list):
        errors.append(f"{ctx.prefix()}: participants must be a list of character ids")

    if errors:
        raise ValidationError("; ".join(errors))
