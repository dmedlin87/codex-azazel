from __future__ import annotations

from pprint import pprint

from bce import queries
import bce.contradictions as contradictions


def main() -> None:
    print("Character IDs:")
    for cid in queries.list_character_ids():
        print(f" - {cid}")

    print("\nEvent IDs:")
    for eid in queries.list_event_ids():
        print(f" - {eid}")

    jesus = queries.get_character("jesus")
    source_ids = sorted({profile.source_id for profile in jesus.source_profiles})
    print("\nJesus source IDs:")
    print(source_ids)

    print("\nJesus trait comparison by source:")
    jesus_comparison = contradictions.compare_character_sources("jesus")
    pprint(jesus_comparison)

    crucifixion = queries.get_event("crucifixion")
    print("\nCrucifixion participants:")
    print(crucifixion.participants)

    print("\nCrucifixion differing accounts:")
    crucifixion_conflicts = contradictions.find_events_with_conflicting_accounts(
        "crucifixion"
    )
    pprint(crucifixion_conflicts)


if __name__ == "__main__":  # pragma: no cover
    main()
