from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import api


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    """Entry point for curation workflow automation commands."""
    parser = argparse.ArgumentParser(
        description="Curation helpers for review queues, guardians, and diff impact.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    queue_parser = subparsers.add_parser(
        "queue", help="Build a prioritized review queue.",
    )
    queue_parser.add_argument(
        "--entity",
        choices=["character", "event"],
        default="character",
        help="Entity type to rank (default: character).",
    )
    queue_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional number of items to return.",
    )

    guardian_parser = subparsers.add_parser(
        "guardian",
        help="Run cluster-aware tag/role alignment audit.",
    )
    guardian_parser.add_argument(
        "--clusters",
        type=int,
        default=6,
        help="Number of clusters to build (default: 6).",
    )
    guardian_parser.add_argument(
        "--support",
        type=float,
        default=0.6,
        help="Support threshold (0-1) for dominant tags/roles (default: 0.6).",
    )

    diff_parser = subparsers.add_parser(
        "diff",
        help="Summarize impact of JSON edits on conflicts/metrics.",
    )
    diff_parser.add_argument("before_path", help="Path to the JSON file before edits.")
    diff_parser.add_argument("after_path", help="Path to the JSON file after edits.")
    diff_parser.add_argument(
        "--entity",
        choices=["character", "event"],
        default="character",
        help="Entity type represented by the JSON files (default: character).",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if exc.code is not None else 2

    try:
        if args.command == "queue":
            result = api.build_curation_review_queue(
                entity_type=args.entity,
                limit=args.limit,
            )
            _print_json(result)
        elif args.command == "guardian":
            result = api.run_cluster_guardian(
                num_clusters=args.clusters,
                support_threshold=args.support,
            )
            _print_json(result)
        elif args.command == "diff":
            before = json.loads(Path(args.before_path).read_text(encoding="utf-8"))
            after = json.loads(Path(args.after_path).read_text(encoding="utf-8"))
            result = api.summarize_json_edit_impact(
                before=before,
                after=after,
                entity_type=args.entity,
            )
            _print_json(result)
        else:  # pragma: no cover - parser ensures command is set
            parser.print_help()
            return 2
    except Exception as exc:  # pragma: no cover - defensive catch for CLI
        print(f"Error: {exc}", file=__import__("sys").stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
