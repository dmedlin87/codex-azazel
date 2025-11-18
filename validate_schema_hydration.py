#!/usr/bin/env python3
"""
Comprehensive schema validation to ensure all characters are fully hydrated.

This script checks for:
1. Missing optional but recommended fields (tags, relationships)
2. Empty or minimal data in required fields
3. Overall completeness of character data
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_character_hydration(char_id: str, data: Dict[str, Any]) -> List[str]:
    """Check if a character is fully hydrated and return any issues found."""
    issues = []

    # Required fields
    if 'id' not in data:
        issues.append(f"{char_id}: Missing 'id' field")
    elif data['id'] != char_id:
        issues.append(f"{char_id}: ID mismatch (file: {char_id}, content: {data['id']})")

    if 'canonical_name' not in data or not data['canonical_name']:
        issues.append(f"{char_id}: Missing or empty 'canonical_name'")

    if 'aliases' not in data:
        issues.append(f"{char_id}: Missing 'aliases' field")
    elif not isinstance(data['aliases'], list):
        issues.append(f"{char_id}: 'aliases' is not a list")
    elif len(data['aliases']) == 0:
        issues.append(f"{char_id}: Empty 'aliases' array (consider adding at least one alias)")

    if 'roles' not in data:
        issues.append(f"{char_id}: Missing 'roles' field")
    elif not isinstance(data['roles'], list):
        issues.append(f"{char_id}: 'roles' is not a list")
    elif len(data['roles']) == 0:
        issues.append(f"{char_id}: Empty 'roles' array (should have at least one role)")

    # Optional but recommended fields (Phase 2+)
    if 'tags' not in data:
        issues.append(f"{char_id}: Missing 'tags' field (recommended for Phase 2+)")
    elif not isinstance(data['tags'], list):
        issues.append(f"{char_id}: 'tags' is not a list")
    elif len(data['tags']) == 0:
        issues.append(f"{char_id}: Empty 'tags' array (consider adding relevant tags)")

    # Optional but recommended fields (Phase 0.5+)
    if 'relationships' not in data:
        issues.append(f"{char_id}: Missing 'relationships' field (recommended for Phase 0.5+)")
    elif not isinstance(data['relationships'], list):
        issues.append(f"{char_id}: 'relationships' is not a list")
    # Note: Empty relationships array is valid if character truly has no documented relationships

    # Source profiles (required, should have at least one)
    if 'source_profiles' not in data:
        issues.append(f"{char_id}: Missing 'source_profiles' field")
    elif not isinstance(data['source_profiles'], list):
        issues.append(f"{char_id}: 'source_profiles' is not a list")
    elif len(data['source_profiles']) == 0:
        issues.append(f"{char_id}: Empty 'source_profiles' array (should have at least one)")
    else:
        # Check each source profile
        for i, profile in enumerate(data['source_profiles']):
            if not isinstance(profile, dict):
                issues.append(f"{char_id}: source_profiles[{i}] is not a dict")
                continue

            if 'source_id' not in profile or not profile['source_id']:
                issues.append(f"{char_id}: source_profiles[{i}] missing 'source_id'")

            if 'traits' not in profile:
                issues.append(f"{char_id}: source_profiles[{i}] missing 'traits' field")
            elif not isinstance(profile['traits'], dict):
                issues.append(f"{char_id}: source_profiles[{i}] 'traits' is not a dict")
            elif len(profile['traits']) == 0:
                issues.append(f"{char_id}: source_profiles[{i}] has empty 'traits' (should have at least one trait)")

            if 'references' not in profile:
                issues.append(f"{char_id}: source_profiles[{i}] missing 'references' field")
            elif not isinstance(profile['references'], list):
                issues.append(f"{char_id}: source_profiles[{i}] 'references' is not a list")
            elif len(profile['references']) == 0:
                issues.append(f"{char_id}: source_profiles[{i}] has empty 'references' (should have at least one reference)")

    return issues

def check_event_hydration(event_id: str, data: Dict[str, Any]) -> List[str]:
    """Check if an event is fully hydrated and return any issues found."""
    issues = []

    # Required fields
    if 'id' not in data:
        issues.append(f"{event_id}: Missing 'id' field")
    elif data['id'] != event_id:
        issues.append(f"{event_id}: ID mismatch (file: {event_id}, content: {data['id']})")

    if 'label' not in data or not data['label']:
        issues.append(f"{event_id}: Missing or empty 'label'")

    if 'participants' not in data:
        issues.append(f"{event_id}: Missing 'participants' field")
    elif not isinstance(data['participants'], list):
        issues.append(f"{event_id}: 'participants' is not a list")
    # Note: Empty participants array might be valid for some events

    # Optional but recommended fields (Phase 2+)
    if 'tags' not in data:
        issues.append(f"{event_id}: Missing 'tags' field (recommended for Phase 2+)")
    elif not isinstance(data['tags'], list):
        issues.append(f"{event_id}: 'tags' is not a list")
    elif len(data['tags']) == 0:
        issues.append(f"{event_id}: Empty 'tags' array (consider adding relevant tags)")

    # Optional but recommended fields (Phase 0.5+)
    if 'parallels' not in data:
        issues.append(f"{event_id}: Missing 'parallels' field (recommended for Phase 0.5+)")
    elif not isinstance(data['parallels'], list):
        issues.append(f"{event_id}: 'parallels' is not a list")
    # Note: Empty parallels array is valid if event has no parallel accounts

    # Accounts (required, should have at least one)
    if 'accounts' not in data:
        issues.append(f"{event_id}: Missing 'accounts' field")
    elif not isinstance(data['accounts'], list):
        issues.append(f"{event_id}: 'accounts' is not a list")
    elif len(data['accounts']) == 0:
        issues.append(f"{event_id}: Empty 'accounts' array (should have at least one)")
    else:
        # Check each account
        for i, account in enumerate(data['accounts']):
            if not isinstance(account, dict):
                issues.append(f"{event_id}: accounts[{i}] is not a dict")
                continue

            if 'source_id' not in account or not account['source_id']:
                issues.append(f"{event_id}: accounts[{i}] missing 'source_id'")

            if 'reference' not in account or not account['reference']:
                issues.append(f"{event_id}: accounts[{i}] missing or empty 'reference'")

            if 'summary' not in account or not account['summary']:
                issues.append(f"{event_id}: accounts[{i}] missing or empty 'summary'")

    return issues

def main():
    """Run comprehensive schema validation."""
    data_root = Path(__file__).parent / 'bce' / 'data'
    char_dir = data_root / 'characters'
    event_dir = data_root / 'events'

    all_issues = []

    # Check characters
    print("=" * 80)
    print("VALIDATING CHARACTER SCHEMA AND HYDRATION")
    print("=" * 80)

    char_files = sorted(char_dir.glob('*.json'))
    print(f"\nFound {len(char_files)} character files\n")

    for char_file in char_files:
        char_id = char_file.stem
        try:
            data = load_json_file(char_file)
            issues = check_character_hydration(char_id, data)
            all_issues.extend(issues)
        except Exception as e:
            issue = f"{char_id}: Failed to load or parse JSON: {e}"
            all_issues.append(issue)
            print(f"ERROR: {issue}")

    # Check events
    print("=" * 80)
    print("VALIDATING EVENT SCHEMA AND HYDRATION")
    print("=" * 80)

    event_files = sorted(event_dir.glob('*.json'))
    print(f"\nFound {len(event_files)} event files\n")

    for event_file in event_files:
        event_id = event_file.stem
        try:
            data = load_json_file(event_file)
            issues = check_event_hydration(event_id, data)
            all_issues.extend(issues)
        except Exception as e:
            issue = f"{event_id}: Failed to load or parse JSON: {e}"
            all_issues.append(issue)
            print(f"ERROR: {issue}")

    # Print summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    if not all_issues:
        print("\n✓ All characters and events are fully hydrated!")
        print("  - All required fields are present")
        print("  - All recommended fields (tags, relationships, parallels) are present")
        print("  - No schema violations found")
        return 0
    else:
        print(f"\n✗ Found {len(all_issues)} issues:\n")

        # Group issues by severity
        missing_required = [i for i in all_issues if 'Missing' in i and 'recommended' not in i]
        missing_recommended = [i for i in all_issues if 'recommended' in i]
        empty_fields = [i for i in all_issues if 'Empty' in i or 'empty' in i]
        other_issues = [i for i in all_issues if i not in missing_required and i not in missing_recommended and i not in empty_fields]

        if missing_required:
            print(f"CRITICAL - Missing Required Fields ({len(missing_required)}):")
            for issue in missing_required:
                print(f"  - {issue}")
            print()

        if empty_fields:
            print(f"WARNING - Empty Fields ({len(empty_fields)}):")
            for issue in empty_fields:
                print(f"  - {issue}")
            print()

        if missing_recommended:
            print(f"INFO - Missing Recommended Fields ({len(missing_recommended)}):")
            for issue in missing_recommended:
                print(f"  - {issue}")
            print()

        if other_issues:
            print(f"OTHER - Other Issues ({len(other_issues)}):")
            for issue in other_issues:
                print(f"  - {issue}")
            print()

        return 1

if __name__ == '__main__':
    exit(main())
