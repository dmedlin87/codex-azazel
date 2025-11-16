from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from bce import queries
from bce import export as export_mod
from bce import dossiers


def _print_json(obj) -> None:
    print(json.dumps(asdict(obj), ensure_ascii=False, indent=2))


def main(argv=None) -> None:
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

    args = parser.parse_args(argv)

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


if __name__ == "__main__":  # pragma: no cover
    main()
