from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from bce import dossiers
from bce import export as export_mod
from bce import queries, storage
from bce import validation


def _print_json(obj) -> None:
    print(json.dumps(asdict(obj), ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="bce",
        description="Biblical Character / Before Canon Engine CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-chars", help="List character IDs")
    show_char = subparsers.add_parser("show-char", help="Show a character by ID")
    show_char.add_argument("char_id")

    show_char_dossier = subparsers.add_parser(
        "show-char-dossier",
        help="Show a JSON dossier for a character",
    )
    show_char_dossier.add_argument("char_id")

    subparsers.add_parser("list-events", help="List event IDs")
    show_event = subparsers.add_parser("show-event", help="Show an event by ID")
    show_event.add_argument("event_id")
    show_event_dossier = subparsers.add_parser(
        "show-event-dossier",
        help="Show a JSON dossier for an event",
    )
    show_event_dossier.add_argument("event_id")
    export_chars = subparsers.add_parser(
        "export-chars", help="Export all characters to a JSON file"
    )
    export_chars.add_argument("output_path")
    export_events = subparsers.add_parser(
        "export-events", help="Export all events to a JSON file"
    )
    export_events.add_argument("output_path")

    subparsers.add_parser(
        "check-data", help="Validate that all data files are loadable",
    )

    subparsers.add_parser(
        "validate-data", help="Run full BCE validation pipeline",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse calls sys.exit() on errors, convert to return code
        return e.code if e.code is not None else 2

    try:
        if args.command == "list-chars":
            for cid in queries.list_character_ids():
                print(cid)
        elif args.command == "show-char":
            char = queries.get_character(args.char_id)
            _print_json(char)
        elif args.command == "show-char-dossier":
            d = dossiers.build_character_dossier(args.char_id)
            print(json.dumps(d, indent=2, sort_keys=True))
        elif args.command == "list-events":
            for eid in queries.list_event_ids():
                print(eid)
        elif args.command == "show-event":
            event = queries.get_event(args.event_id)
            _print_json(event)
        elif args.command == "show-event-dossier":
            d = dossiers.build_event_dossier(args.event_id)
            print(json.dumps(d, indent=2, sort_keys=True))
        elif args.command == "export-chars":
            export_mod.export_all_characters(args.output_path)
            print(f"Exported characters to {args.output_path}")
        elif args.command == "export-events":
            export_mod.export_all_events(args.output_path)
            print(f"Exported events to {args.output_path}")
        elif args.command == "check-data":
            # Reuse storage-level loading to verify JSON + encoding correctness.
            for cid in storage.list_character_ids():
                storage.load_character(cid)
            for eid in storage.list_event_ids():
                storage.load_event(eid)
            print("All character and event data files loaded successfully.")
        elif args.command == "validate-data":
            report = validation.run_validation()
            if report.skipped:
                reason = report.reason or "No reason provided"
                print(f"Validation skipped: {reason}")
                return 0

            if report.errors:
                print("Validation errors detected:", file=sys.stderr)
                for message in report.errors:
                    print(f"- {message}", file=sys.stderr)

            if report.warnings:
                print("Validation warnings:")
                for message in report.warnings:
                    print(f"- {message}")

            if report.errors:
                return 1

            if report.warnings:
                print("Validation completed with warnings but no errors.")
            else:
                print("Validation succeeded with no errors.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
