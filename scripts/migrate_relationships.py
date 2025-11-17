#!/usr/bin/env python3
"""Migration script to normalize relationship data format.

This script converts character relationship data from the legacy grouped
format (objects with "family", "mentors", etc. keys) to the canonical
flat array format with standardized field names.

Legacy format (jesus.json):
    {
      "relationships": {
        "family": [
          {"name": "Mary", "relationship": "mother", ...}
        ],
        "mentors": [...]
      }
    }

Canonical format (peter.json):
    {
      "relationships": [
        {"character_id": "mary", "type": "mother", ...}
      ]
    }

Usage:
    python scripts/migrate_relationships.py [--dry-run] [--character CHAR_ID]

Options:
    --dry-run: Show what would be changed without modifying files
    --character: Only migrate specific character (default: all)
    --backup: Create .bak files before modifying (default: true)
    --no-backup: Skip creating backup files
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def normalize_name_to_id(name: str) -> str:
    """Convert a display name to a character ID.

    Examples:
        >>> normalize_name_to_id("Mary")
        'mary'
        >>> normalize_name_to_id("James and siblings")
        'james_and_siblings'
        >>> normalize_name_to_id("John the Baptist")
        'john_the_baptist'
    """
    # Convert to lowercase and replace spaces with underscores
    char_id = name.lower().strip()
    char_id = char_id.replace(" ", "_")

    # Remove common articles and prepositions at the start
    for prefix in ["the_", "of_", "a_", "an_"]:
        if char_id.startswith(prefix):
            char_id = char_id[len(prefix):]

    # Clean up multiple underscores
    while "__" in char_id:
        char_id = char_id.replace("__", "_")

    return char_id.strip("_")


def migrate_relationships(relationships: Any) -> List[Dict[str, Any]]:
    """Convert relationships from any format to canonical array format.

    Parameters:
        relationships: Either a dict (grouped format), list (array format),
                      or None

    Returns:
        List of relationship dicts in canonical format
    """
    if relationships is None:
        return []

    # Already in array format
    if isinstance(relationships, list):
        normalized = []
        for rel in relationships:
            if not isinstance(rel, dict):
                continue

            # Ensure it has the canonical field names
            migrated = {}

            # Handle character_id vs name
            if "character_id" in rel:
                migrated["character_id"] = rel["character_id"]
            elif "name" in rel:
                # Convert display name to ID (best effort)
                migrated["character_id"] = normalize_name_to_id(rel["name"])
            else:
                # Skip relationships without identifiers
                continue

            # Handle type vs relationship
            if "type" in rel:
                migrated["type"] = rel["type"]
            elif "relationship" in rel:
                migrated["type"] = rel["relationship"]
            else:
                # Skip relationships without type
                continue

            # Copy over other fields
            for key in ["sources", "references", "notes"]:
                if key in rel:
                    migrated[key] = rel[key]

            normalized.append(migrated)

        return normalized

    # Grouped format (dict with category keys)
    if isinstance(relationships, dict):
        flat = []

        for category, items in relationships.items():
            if not isinstance(items, list):
                continue

            for rel in items:
                if not isinstance(rel, dict):
                    continue

                migrated = {}

                # Extract character identifier
                if "character_id" in rel:
                    migrated["character_id"] = rel["character_id"]
                elif "name" in rel:
                    migrated["character_id"] = normalize_name_to_id(rel["name"])
                else:
                    continue

                # Extract relationship type
                if "type" in rel:
                    migrated["type"] = rel["type"]
                elif "relationship" in rel:
                    migrated["type"] = rel["relationship"]
                else:
                    continue

                # Copy over other fields
                for key in ["sources", "references", "notes"]:
                    if key in rel:
                        migrated[key] = rel[key]

                flat.append(migrated)

        return flat

    # Unknown format
    return []


def migrate_character_file(
    file_path: Path,
    dry_run: bool = False,
    backup: bool = True
) -> tuple[bool, str]:
    """Migrate a single character file.

    Parameters:
        file_path: Path to character JSON file
        dry_run: If True, don't modify the file
        backup: If True, create .bak file before modifying

    Returns:
        Tuple of (was_modified, message)
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Failed to read: {e}"

    # Check if relationships need migration
    relationships = data.get("relationships")

    if relationships is None:
        return False, "No relationships field"

    if isinstance(relationships, list):
        # Check if already using canonical field names
        needs_migration = False
        for rel in relationships:
            if isinstance(rel, dict):
                if "name" in rel or "relationship" in rel:
                    needs_migration = True
                    break

        if not needs_migration:
            return False, "Already in canonical format"

    # Perform migration
    migrated_relationships = migrate_relationships(relationships)

    if migrated_relationships == relationships:
        return False, "No changes needed"

    # Update data
    data["relationships"] = migrated_relationships

    message_parts = []

    if isinstance(relationships, dict):
        message_parts.append(f"Converted grouped format to flat array")
        message_parts.append(f"({len(migrated_relationships)} relationships)")
    else:
        message_parts.append(f"Normalized field names")

    message = " ".join(message_parts)

    if dry_run:
        return True, f"[DRY RUN] Would migrate: {message}"

    # Create backup if requested
    if backup:
        backup_path = file_path.with_suffix(".json.bak")
        with file_path.open("r", encoding="utf-8") as src:
            with backup_path.open("w", encoding="utf-8") as dst:
                dst.write(src.read())

    # Write migrated data
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True, f"Migrated: {message}"


def main():
    """Run migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate character relationship data to canonical format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--character",
        type=str,
        help="Only migrate specific character ID"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup files"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Path to data directory (default: bce/data)"
    )

    args = parser.parse_args()

    # Determine data directory
    if args.data_dir:
        data_dir = args.data_dir
    else:
        # Assume script is in scripts/ directory
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "bce" / "data"

    char_dir = data_dir / "characters"

    if not char_dir.exists():
        print(f"Error: Characters directory not found: {char_dir}", file=sys.stderr)
        return 1

    # Get list of character files to process
    if args.character:
        file_path = char_dir / f"{args.character}.json"
        if not file_path.exists():
            print(f"Error: Character file not found: {file_path}", file=sys.stderr)
            return 1
        files_to_process = [file_path]
    else:
        files_to_process = sorted(char_dir.glob("*.json"))

    # Process files
    modified_count = 0
    skipped_count = 0
    error_count = 0

    for file_path in files_to_process:
        char_id = file_path.stem
        was_modified, message = migrate_character_file(
            file_path,
            dry_run=args.dry_run,
            backup=not args.no_backup
        )

        if was_modified:
            print(f"✓ {char_id}: {message}")
            modified_count += 1
        elif "Failed" in message or "Error" in message:
            print(f"✗ {char_id}: {message}")
            error_count += 1
        else:
            # Uncomment to see skipped files
            # print(f"  {char_id}: {message}")
            skipped_count += 1

    # Summary
    print()
    print(f"Summary:")
    print(f"  Modified: {modified_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"  Errors:   {error_count}")

    if args.dry_run and modified_count > 0:
        print()
        print("Re-run without --dry-run to apply changes")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
