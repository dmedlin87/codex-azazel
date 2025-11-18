"""
Auto-Tagging Plugin Example

This plugin demonstrates how to use BCE's hooks system to automatically
tag characters based on their roles.

When a character with the "apostle" role is saved, this plugin automatically
adds the "apostle" tag if it's not already present.

Usage:
    # In your code, import and the hook will be registered
    import examples.plugins.auto_tag_apostles

    # Or manually run the setup function
    from examples.plugins.auto_tag_apostles import setup_auto_tagging
    setup_auto_tagging()

    # Now when you save a character with apostle role, it gets auto-tagged
    from bce import storage
    from bce.models import Character, SourceProfile

    peter = Character(
        id="peter",
        canonical_name="Peter",
        aliases=["Simon Peter"],
        roles=["apostle", "disciple"],
        tags=[],  # Empty tags - will be auto-populated
        relationships=[],
        source_profiles=[
            SourceProfile(
                source_id="mark",
                traits={"role": "leader among disciples"},
                references=["Mark 1:16"]
            )
        ]
    )

    storage.save_character(peter)
    # Peter now has "apostle" tag automatically added
"""

from bce.hooks import hook, HookPoint, HookContext


@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=50)
def auto_tag_apostles(ctx: HookContext) -> HookContext:
    """Automatically tag characters who are apostles"""
    character = ctx.data

    # Check if character has "apostle" role
    if "apostle" in character.roles:
        # Add "apostle" tag if not already present
        if "apostle" not in character.tags:
            character.tags.append("apostle")
            print(f"✓ Auto-tagged {character.id} with 'apostle'")

    ctx.data = character
    return ctx


@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=51)
def auto_tag_gospel_authors(ctx: HookContext) -> HookContext:
    """Automatically tag gospel authors"""
    character = ctx.data

    # Check if character has "gospel_author" role
    if "gospel_author" in character.roles:
        if "gospel_author" not in character.tags:
            character.tags.append("gospel_author")
            if "evangelist" not in character.tags:
                character.tags.append("evangelist")
            print(f"✓ Auto-tagged {character.id} with 'gospel_author' and 'evangelist'")

    ctx.data = character
    return ctx


def setup_auto_tagging():
    """
    Setup function for programmatic registration

    Note: If you import this module, the @hook decorators will automatically
    register the hooks. This function is provided for manual setup if needed.
    """
    print("Auto-tagging hooks registered")
    print("  - auto_tag_apostles (priority 50)")
    print("  - auto_tag_gospel_authors (priority 51)")


# Auto-setup on import
print("📌 Auto-tagging plugin loaded")
