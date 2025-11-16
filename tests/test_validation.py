from __future__ import annotations

from bce.validation import validate_all


def test_validate_all_has_no_errors() -> None:
    errors = validate_all()
    assert errors == [], f"Validation errors: {errors}"
