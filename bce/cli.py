from __future__ import annotations

import argparse
import sys
from typing import Iterable

from .dossiers import build_character_dossier, build_event_dossier
from .export import dossier_to_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and export BCE dossiers")
    parser.add_argument("kind", choices=["character", "event"], help="Type of dossier to build")
    parser.add_argument("dossier_id", help="ID of the dossier to build")
    parser.add_argument(
        "-f",
        "--format",
        choices=["markdown"],
        default="markdown",
        help="Output format (currently only 'markdown')",
    )

    args = parser.parse_args(argv)

    try:
        if args.kind == "character":
            dossier = build_character_dossier(args.dossier_id)
        else:
            dossier = build_event_dossier(args.dossier_id)
    except (KeyError, FileNotFoundError):
        print(f"Error: dossier with id '{args.dossier_id}' not found", file=sys.stderr)
        return 1

    if args.format == "markdown":
        output = dossier_to_markdown(dossier)
        print(output)
    else:
        # This branch should not be reachable due to argparse choices, but
        # keep it defensive in case of future extension.
        print(f"Error: unsupported format '{args.format}'", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not import
    raise SystemExit(main())
