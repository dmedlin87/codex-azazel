#!/usr/bin/env python3
"""
Script to add missing optional but recommended fields to characters and events.

This script adds:
- Empty 'tags' arrays to characters and events missing them
- Empty 'relationships' arrays to characters missing them
- Empty 'parallels' arrays to events missing them
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file with consistent formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Add trailing newline

def hydrate_character(char_file: Path) -> bool:
    """Add missing fields to a character. Returns True if changes were made."""
    char_id = char_file.stem
    data = load_json_file(char_file)
    changed = False

    # Add tags if missing
    if 'tags' not in data:
        # Insert tags after roles, before relationships
        # We need to reconstruct the dict to control field order
        new_data = {}
        for key in ['id', 'canonical_name', 'aliases', 'roles']:
            if key in data:
                new_data[key] = data[key]

        new_data['tags'] = []
        changed = True

        for key in data:
            if key not in new_data:
                new_data[key] = data[key]

        data = new_data

    # Add relationships if missing
    if 'relationships' not in data:
        # Insert relationships after tags, before source_profiles
        new_data = {}
        for key in ['id', 'canonical_name', 'aliases', 'roles', 'tags']:
            if key in data:
                new_data[key] = data[key]

        new_data['relationships'] = []
        changed = True

        for key in data:
            if key not in new_data:
                new_data[key] = data[key]

        data = new_data

    if changed:
        save_json_file(char_file, data)
        print(f"✓ Updated {char_id}")

    return changed

def hydrate_event(event_file: Path) -> bool:
    """Add missing fields to an event. Returns True if changes were made."""
    event_id = event_file.stem
    data = load_json_file(event_file)
    changed = False

    # Add tags if missing
    if 'tags' not in data:
        # Insert tags after participants, before parallels
        new_data = {}
        for key in ['id', 'label', 'participants']:
            if key in data:
                new_data[key] = data[key]

        new_data['tags'] = []
        changed = True

        for key in data:
            if key not in new_data:
                new_data[key] = data[key]

        data = new_data

    # Add parallels if missing
    if 'parallels' not in data:
        # Insert parallels after tags, before accounts
        new_data = {}
        for key in ['id', 'label', 'participants', 'tags']:
            if key in data:
                new_data[key] = data[key]

        new_data['parallels'] = []
        changed = True

        for key in data:
            if key not in new_data:
                new_data[key] = data[key]

        data = new_data

    if changed:
        save_json_file(event_file, data)
        print(f"✓ Updated {event_id}")

    return changed

def main():
    """Run hydration on all characters and events."""
    data_root = Path(__file__).parent / 'bce' / 'data'
    char_dir = data_root / 'characters'
    event_dir = data_root / 'events'

    print("=" * 80)
    print("HYDRATING CHARACTERS")
    print("=" * 80)

    char_files = sorted(char_dir.glob('*.json'))
    char_updated = 0

    for char_file in char_files:
        try:
            if hydrate_character(char_file):
                char_updated += 1
        except Exception as e:
            print(f"✗ Error updating {char_file.stem}: {e}")

    print(f"\nUpdated {char_updated} of {len(char_files)} characters")

    print("\n" + "=" * 80)
    print("HYDRATING EVENTS")
    print("=" * 80)

    event_files = sorted(event_dir.glob('*.json'))
    event_updated = 0

    for event_file in event_files:
        try:
            if hydrate_event(event_file):
                event_updated += 1
        except Exception as e:
            print(f"✗ Error updating {event_file.stem}: {e}")

    print(f"\nUpdated {event_updated} of {len(event_files)} events")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total characters updated: {char_updated}")
    print(f"Total events updated: {event_updated}")
    print(f"Total files updated: {char_updated + event_updated}")

if __name__ == '__main__':
    main()
