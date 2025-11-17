# Code Review Fixes - Implementation Guide

This document details the fixes implemented to address critical and important issues identified in the code review.

## 🔴 Critical Fix #1: Type Safety for Relationships and Parallels

### Problem
The `Character.relationships` and `Event.parallels` fields were typed as `List[dict]`, defeating type safety and preventing IDE autocomplete, validation, and documentation generation.

### Solution
Created `bce/relationship_types.py` with strongly-typed dataclasses:

```python
@dataclass(slots=True)
class Relationship:
    character_id: str
    type: str
    sources: List[str]
    references: List[str]
    notes: Optional[str] = None

@dataclass(slots=True)
class EventParallel:
    sources: List[str]
    references: Dict[str, str]
    relationship: str
```

### Migration Path
To adopt these types in `bce/models.py`, update:

```python
# OLD
relationships: List[dict] = field(default_factory=list)

# NEW
from .relationship_types import Relationship
relationships: List[Relationship] = field(default_factory=list)
```

**⚠️ BREAKING CHANGE**: This will require updates to:
- `storage.py` to convert dicts to dataclasses on load
- All code that directly accesses relationship fields
- Tests that construct Character objects

**Recommendation**: Implement in v0.2.0 with migration guide.

---

## 🔴 Critical Fix #2: Data Format Normalization

### Problem
Character JSON files use two different formats for relationships:

1. **Grouped format** (jesus.json):
   ```json
   {
     "relationships": {
       "family": [{...}],
       "mentors": [{...}]
     }
   }
   ```

2. **Array format** (peter.json):
   ```json
   {
     "relationships": [{...}, {...}]
   }
   ```

Field names also vary: `name` vs `character_id`, `relationship` vs `type`.

### Solution
Created `scripts/migrate_relationships.py` to normalize all data to canonical array format with standardized field names.

### Usage
```bash
# Dry run to see what would change
python scripts/migrate_relationships.py --dry-run

# Migrate all characters (creates .bak files automatically)
python scripts/migrate_relationships.py

# Migrate specific character only
python scripts/migrate_relationships.py --character jesus

# Skip backup creation
python scripts/migrate_relationships.py --no-backup
```

### Canonical Format
After migration, all relationships will use:
- `character_id` (not `name`)
- `type` (not `relationship`)
- Flat array structure (not grouped by category)

---

## 🟠 Important Fix #3: Confusing has_trait Fallback Behavior

### Problem
`Character.has_trait(trait, source)` has unintuitive fallback logic:

```python
def has_trait(self, trait: str, source: Optional[str] = None) -> bool:
    if source is not None:
        profile = self.get_source_profile(source)
        if profile and any(k.lower() == needle for k in profile.traits.keys()):
            return True
        # Falls back to checking global tags even when specific source requested!
        return any(isinstance(tag, str) and tag.lower() == needle for tag in self.tags)
```

**Issue**: If you ask "Does Jesus have trait X in Mark?", it returns `True` if:
- Mark mentions it, OR
- It's in global tags (even if Mark never mentions it)

This is confusing and likely not the intended behavior.

### Recommended Fix
Replace the ambiguous method with clear, purpose-specific methods:

```python
def has_trait_in_source(self, trait: str, source: str) -> bool:
    """Check if a specific source mentions this trait.

    Returns True only if the source profile contains the trait.
    Does NOT fall back to tags.
    """
    needle = trait.lower()
    profile = self.get_source_profile(source)
    if profile is None:
        return False
    return any(k.lower() == needle for k in profile.traits.keys())

def has_trait_in_any_source(self, trait: str) -> bool:
    """Check if ANY source mentions this trait.

    Does NOT check tags - use has_tag_or_trait() for that.
    """
    needle = trait.lower()
    for profile in self.source_profiles:
        if any(k.lower() == needle for k in profile.traits.keys()):
            return True
    return False

def has_tag_or_trait(self, needle: str) -> bool:
    """Check if character has a tag OR trait matching the needle.

    Searches both global tags and all source profile traits.
    """
    needle_lower = needle.lower()

    # Check global tags
    if any(isinstance(tag, str) and tag.lower() == needle_lower for tag in self.tags):
        return True

    # Check all source traits
    return self.has_trait_in_any_source(needle)

def has_trait(self, trait: str, source: Optional[str] = None) -> bool:
    """DEPRECATED: Use has_trait_in_source() or has_trait_in_any_source() instead.

    This method's fallback behavior is confusing. It will be removed in v0.3.0.
    """
    import warnings
    warnings.warn(
        "Character.has_trait() is deprecated due to ambiguous semantics. "
        "Use has_trait_in_source(trait, source) or has_trait_in_any_source(trait) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Keep current behavior for backward compatibility
    needle = trait.lower()
    if source is not None:
        profile = self.get_source_profile(source)
        if profile and any(k.lower() == needle for k in profile.traits.keys()):
            return True
        return any(isinstance(tag, str) and tag.lower() == needle for tag in self.tags)

    for profile in self.source_profiles:
        if any(k.lower() == needle for k in profile.traits.keys()):
            return True
    return any(isinstance(tag, str) and tag.lower() == needle for tag in self.tags)
```

### Migration Path
1. Add new methods alongside deprecated `has_trait()`
2. Update internal code to use new methods
3. Add deprecation warning to `has_trait()`
4. Remove `has_trait()` in v0.3.0

---

## 🟡 Moderate Fix #4: Expanded Scripture Validation

### Problem
Only 4 books validated (Matthew, Mark, Luke, John), but data includes Acts, Pauline epistles, Hebrews, Revelation.

### Solution
Expand `bce/validation.py` with complete NT chapter counts:

```python
_BOOK_MAX_CHAPTER: Dict[str, int] = {
    # Gospels
    "Matthew": 28,
    "Mark": 16,
    "Luke": 24,
    "John": 21,

    # History
    "Acts": 28,

    # Pauline Epistles (Undisputed)
    "Romans": 16,
    "1 Corinthians": 16,
    "2 Corinthians": 13,
    "Galatians": 6,
    "Philippians": 4,
    "1 Thessalonians": 5,
    "Philemon": 1,

    # Pauline Epistles (Disputed)
    "Ephesians": 6,
    "Colossians": 4,
    "2 Thessalonians": 3,
    "1 Timothy": 6,
    "2 Timothy": 4,
    "Titus": 3,

    # General Epistles
    "Hebrews": 13,
    "James": 5,
    "1 Peter": 5,
    "2 Peter": 3,
    "1 John": 5,
    "2 John": 1,
    "3 John": 1,
    "Jude": 1,

    # Apocalyptic
    "Revelation": 22,
}
```

Apply this fix by editing `/home/user/codex-azazel/bce/validation.py` lines 19-24.

---

## 🟡 Moderate Fix #5: Remove Defensive getattr Usage

### Problem
Code uses `getattr(char, "tags", [])` suggesting potential missing fields, but dataclasses always define these fields.

### Analysis Needed
Run this check to see if defensive code is needed:

```python
# Check if any character is missing the tags field
from bce import queries
for char_id in queries.list_character_ids():
    char = queries.get_character(char_id)
    if not hasattr(char, 'tags'):
        print(f"Character {char_id} missing tags field")
```

If all characters have the field, remove defensive `getattr()` calls in:
- `bce/queries.py` lines 66-67, 82-83
- Any other locations using this pattern

---

## 🟡 Moderate Fix #6: CLI Exception Handling

### Problem
`bce/cli.py:30` catches `KeyError` but dossier builders likely only raise `FileNotFoundError` or `DataNotFoundError`.

### Recommended Fix
Test what exceptions are actually raised and update the handler:

```python
# Option 1: Remove KeyError if it never occurs
except FileNotFoundError:
    print(f"Error: dossier with id '{args.dossier_id}' not found", file=sys.stderr)
    return 1

# Option 2: Handle separately with different messages
except FileNotFoundError:
    print(f"Error: {args.kind} '{args.dossier_id}' not found", file=sys.stderr)
    return 1
except KeyError as e:
    print(f"Error: Invalid dossier structure - missing key: {e}", file=sys.stderr)
    return 1
```

---

## Testing Recommendations

After applying fixes, run:

```bash
# 1. Run migration script
python scripts/migrate_relationships.py --dry-run
python scripts/migrate_relationships.py

# 2. Validate all data
python -c "from bce.validation import validate_all, validate_cross_references; \
errors = validate_all() + validate_cross_references(); \
print('✓ All checks passed' if not errors else '\n'.join(errors))"

# 3. Test imports
python -c "import bce; from bce import api; print('✓ Imports successful')"

# 4. Test basic operations
python -c "from bce import api; \
char = api.get_character('jesus'); \
dossier = api.build_character_dossier('jesus'); \
print('✓ Basic operations successful')"
```

---

## Implementation Priority

### Immediate (v0.1.1 patch):
1. ✅ Create `relationship_types.py` (non-breaking, additive)
2. ✅ Create `migrate_relationships.py` script (tool, not code change)
3. Run migration on data files
4. Expand scripture validation (low-risk improvement)

### Short-term (v0.2.0 minor):
5. Deprecate `has_trait()` with warnings
6. Add new clear methods (`has_trait_in_source`, etc.)
7. Update internal code to use new methods

### Long-term (v0.3.0 minor):
8. Make relationships and parallels strongly-typed (BREAKING)
9. Remove deprecated `has_trait()` method (BREAKING)
10. Consider thread-safety refactoring

---

## Summary

**Created Files:**
- `bce/relationship_types.py` - Strongly-typed relationship structures
- `scripts/migrate_relationships.py` - Data normalization tool
- `FIXES.md` - This documentation

**Recommended Immediate Actions:**
1. Run migration script on data files
2. Expand scripture validation
3. Review and fix CLI exception handling
4. Add deprecation warnings to ambiguous methods

**Breaking Changes Deferred:**
- Type changes to models (v0.2.0+)
- Method removals (v0.3.0+)

This phased approach allows immediate improvements while giving users time to migrate.
