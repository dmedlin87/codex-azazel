from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bce.dossiers import build_character_dossier
from bce.export import dossier_to_markdown


EXAMPLE_CHARACTER_ID = "jesus"


def main() -> int:
    char_id = EXAMPLE_CHARACTER_ID
    try:
        dossier = build_character_dossier(char_id)
    except Exception as exc:
        print(
            f"Error: could not build character dossier for '{char_id}': {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"=== Character dossier: {char_id} ===")
    print(dossier_to_markdown(dossier))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
