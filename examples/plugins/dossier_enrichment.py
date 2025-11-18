"""
Dossier Enrichment Plugin Example

This plugin demonstrates how to use the DOSSIER_ENRICH hook to add custom
fields to character and event dossiers.

This example adds external resource links (Wikipedia, Bible Gateway, etc.) to
every character dossier.

Usage:
    # Import to activate
    import examples.plugins.dossier_enrichment

    # Now build a dossier and it will have external_resources field
    from bce import api
    dossier = api.build_character_dossier("jesus")
    print(dossier["external_resources"])
    # {
    #   "wikipedia": "https://en.wikipedia.org/wiki/Jesus",
    #   "bible_gateway": "https://www.biblegateway.com/...",
    #   "scholarly_articles": "https://scholar.google.com/..."
    # }
"""

from bce.hooks import hook, HookPoint, HookContext
from urllib.parse import quote


@hook(HookPoint.DOSSIER_ENRICH, priority=100)
def add_external_links(ctx: HookContext) -> HookContext:
    """Add external resource links to dossiers"""
    dossier = ctx.data
    entity_type = ctx.metadata.get("entity_type")

    if entity_type == "character":
        character = ctx.metadata.get("character")
        if character:
            # Add external resources section
            dossier["external_resources"] = {
                "wikipedia": f"https://en.wikipedia.org/wiki/{quote(character.canonical_name)}",
                "bible_gateway": f"https://www.biblegateway.com/quicksearch/?quicksearch={quote(character.canonical_name)}",
                "scholarly_articles": f"https://scholar.google.com/scholar?q={quote(character.canonical_name)}+biblical",
                "blue_letter_bible": f"https://www.blueletterbible.org/search/search.cfm?Criteria={quote(character.canonical_name)}&t=KJV"
            }

    elif entity_type == "event":
        event = ctx.metadata.get("event")
        if event:
            # Add external resources for events
            dossier["external_resources"] = {
                "wikipedia": f"https://en.wikipedia.org/wiki/{quote(event.label)}",
                "scholarly_articles": f"https://scholar.google.com/scholar?q={quote(event.label)}+biblical"
            }

    ctx.data = dossier
    return ctx


@hook(HookPoint.DOSSIER_ENRICH, priority=101)
def add_statistics(ctx: HookContext) -> HookContext:
    """Add statistics to character dossiers"""
    dossier = ctx.data
    entity_type = ctx.metadata.get("entity_type")

    if entity_type == "character":
        # Calculate statistics
        source_count = len(dossier.get("source_ids", []))
        total_traits = sum(
            len(traits)
            for traits in dossier.get("traits_by_source", {}).values()
        )
        total_references = sum(
            len(refs)
            for refs in dossier.get("references_by_source", {}).values()
        )
        conflict_count = len(dossier.get("trait_conflicts", {}))

        dossier["statistics"] = {
            "source_count": source_count,
            "total_traits": total_traits,
            "total_references": total_references,
            "conflict_count": conflict_count,
            "avg_traits_per_source": round(total_traits / source_count, 2) if source_count > 0 else 0
        }

    elif entity_type == "event":
        # Calculate event statistics
        account_count = len(dossier.get("accounts", []))
        participant_count = len(dossier.get("participants", []))
        conflict_count = len(dossier.get("account_conflicts", {}))

        dossier["statistics"] = {
            "account_count": account_count,
            "participant_count": participant_count,
            "conflict_count": conflict_count
        }

    ctx.data = dossier
    return ctx


def setup_enrichment():
    """Setup function for programmatic registration"""
    print("Dossier enrichment hooks registered")
    print("  - add_external_links (priority 100)")
    print("  - add_statistics (priority 101)")


# Auto-setup on import
print("📌 Dossier enrichment plugin loaded")
