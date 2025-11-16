from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bce.dossiers import build_character_dossier, build_event_dossier
from bce.export import dossier_to_markdown


def main() -> int:
    # Build a sample character dossier.
    char_dossier = build_character_dossier("jesus")
    # Build a sample event dossier.
    event_dossier = build_event_dossier("crucifixion")

    print("# Character dossier: jesus")
    print(dossier_to_markdown(char_dossier))
    print("\n---\n")
    print("# Event dossier: crucifixion")
    print(dossier_to_markdown(event_dossier))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
