# Hooks and Plugins Guide

**Status**: Implemented (Phase 7.1)
**Last Updated**: 2025-11-18

## Overview

BCE's hooks system provides a powerful, non-invasive way to extend functionality without modifying core code. Hooks allow you to:

- **Intercept** data lifecycle events (load, save, build)
- **Modify** data as it flows through BCE
- **Enrich** dossiers with custom fields
- **Validate** data with custom rules
- **Abort** operations based on conditions
- **Monitor** BCE operations for logging/debugging

All hooks are **opt-in** and have **minimal performance overhead** when not in use.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Available Hook Points](#available-hook-points)
3. [Hook Registration](#hook-registration)
4. [Hook Context](#hook-context)
5. [Priority and Ordering](#priority-and-ordering)
6. [Example Hooks](#example-hooks)
7. [Plugin Development](#plugin-development)
8. [Best Practices](#best-practices)
9. [Performance Considerations](#performance-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Simple Hook Example

```python
from bce.hooks import hook, HookPoint

# Register a hook using the decorator
@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def auto_tag_apostles(ctx):
    """Automatically tag apostles"""
    character = ctx.data

    if "apostle" in character.roles and "apostle" not in character.tags:
        character.tags.append("apostle")
        print(f"✓ Auto-tagged {character.id} with 'apostle'")

    ctx.data = character
    return ctx

# Now when you save characters, they'll be auto-tagged
from bce import storage
peter = storage.load_character("peter")
storage.save_character(peter)  # Hook triggers here
```

### Dossier Enrichment Example

```python
from bce.hooks import hook, HookPoint

@hook(HookPoint.DOSSIER_ENRICH)
def add_external_links(ctx):
    """Add external resource links"""
    dossier = ctx.data
    character = ctx.metadata.get("character")

    if character:
        dossier["external_resources"] = {
            "wikipedia": f"https://en.wikipedia.org/wiki/{character.canonical_name}",
            "bible_gateway": f"https://www.biblegateway.com/quicksearch/?quicksearch={character.canonical_name}"
        }

    ctx.data = dossier
    return ctx

# Now all dossiers will have external_resources field
from bce import dossiers
jesus_dossier = dossiers.build_character_dossier("jesus")
print(jesus_dossier["external_resources"])
```

---

## Available Hook Points

### Data Lifecycle Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `BEFORE_CHARACTER_LOAD` | Before loading character from JSON | Validate ID, redirect loads, logging |
| `AFTER_CHARACTER_LOAD` | After loading character, before returning | Modify character, add computed fields |
| `BEFORE_CHARACTER_SAVE` | Before saving character to JSON | Validate data, auto-tag, prevent saves |
| `AFTER_CHARACTER_SAVE` | After successful save | Logging, cache invalidation, triggers |
| `BEFORE_EVENT_LOAD` | Before loading event from JSON | Same as character hooks |
| `AFTER_EVENT_LOAD` | After loading event | Same as character hooks |
| `BEFORE_EVENT_SAVE` | Before saving event | Same as character hooks |
| `AFTER_EVENT_SAVE` | After successful save | Same as character hooks |

### Dossier Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `BEFORE_DOSSIER_BUILD` | Before building dossier | Skip expensive builds, redirect |
| `DOSSIER_ENRICH` | After dossier built, before returning | Add custom fields, external data |
| `AFTER_DOSSIER_BUILD` | After dossier fully built | Post-processing, caching |

### Query Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `BEFORE_QUERY` | Before executing query | Query modification, auth checks |
| `AFTER_QUERY` | After query completes | Result transformation |
| `CACHE_HIT` | When cached data is returned | Monitoring, analytics |
| `CACHE_MISS` | When data must be loaded | Monitoring, warm cache |

### Search Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `BEFORE_SEARCH` | Before search executes | Query rewriting, auth |
| `AFTER_SEARCH` | After search completes | Result filtering |
| `SEARCH_RESULT_FILTER` | For each search result | Custom filtering logic |
| `SEARCH_RESULT_RANK` | During result ranking | Custom ranking algorithms |

### Validation Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `BEFORE_VALIDATION` | Before validation runs | Add custom checks |
| `AFTER_VALIDATION` | After validation completes | Process errors |
| `VALIDATION_ERROR` | When validation fails | Error handling, notifications |

### Export Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `BEFORE_EXPORT` | Before export starts | Preprocessing |
| `AFTER_EXPORT` | After export completes | Postprocessing |
| `EXPORT_FORMAT_RESOLVE` | When determining export format | Add custom formats |

### Conflict Detection Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `BEFORE_CONFLICT_DETECTION` | Before detecting conflicts | Skip expensive checks |
| `AFTER_CONFLICT_DETECTION` | After conflicts found | Custom processing |
| `CONFLICT_SEVERITY_SCORE` | When scoring conflict severity | Custom severity logic |

### System Hooks

| Hook Point | When Triggered | Use Cases |
|------------|----------------|-----------|
| `STARTUP` | When BCE initializes | Setup, warm cache |
| `SHUTDOWN` | When BCE shuts down | Cleanup, save state |
| `CONFIG_CHANGE` | When configuration changes | Reload, invalidate cache |

---

## Hook Registration

### Using the @hook Decorator

The simplest way to register hooks:

```python
from bce.hooks import hook, HookPoint

@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def my_handler(ctx):
    # Your logic here
    return ctx
```

### Manual Registration

For more control:

```python
from bce.hooks import HookRegistry, HookPoint

def my_handler(ctx):
    return ctx

HookRegistry.register(
    HookPoint.BEFORE_CHARACTER_SAVE,
    my_handler,
    priority=100
)
```

### Unregistering Hooks

```python
HookRegistry.unregister(HookPoint.BEFORE_CHARACTER_SAVE, my_handler)
```

### Clearing All Hooks

Useful for testing:

```python
HookRegistry.clear_all()
```

### Disabling/Enabling Hooks

For performance-critical sections:

```python
from bce.hooks import HookRegistry

HookRegistry.disable()  # Hooks won't execute
# ... perform operations ...
HookRegistry.enable()   # Re-enable hooks
```

---

## Hook Context

Every hook receives a `HookContext` object:

```python
from bce.hooks import HookContext

@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def my_handler(ctx: HookContext):
    # ctx.hook_point: The hook that triggered (enum)
    # ctx.data: The primary data (can be modified)
    # ctx.metadata: Additional read-only context
    # ctx.abort: Set to True to abort operation

    print(f"Hook: {ctx.hook_point}")
    print(f"Data: {ctx.data}")
    print(f"Metadata: {ctx.metadata}")

    # Modify data
    ctx.data = transform(ctx.data)

    # Or abort
    if should_abort(ctx.data):
        ctx.abort = True

    return ctx
```

### Data Field

The `data` field contains different things depending on the hook:

| Hook | ctx.data Contains |
|------|-------------------|
| `BEFORE_CHARACTER_LOAD` | `{"char_id": "..."}` dict |
| `AFTER_CHARACTER_LOAD` | `Character` object |
| `BEFORE_CHARACTER_SAVE` | `Character` object |
| `AFTER_CHARACTER_SAVE` | `Character` object |
| `DOSSIER_ENRICH` | Dossier dict |
| `BEFORE_QUERY` | Query parameters |
| `AFTER_QUERY` | Query results |

### Metadata Field

The `metadata` field provides additional context:

```python
@hook(HookPoint.DOSSIER_ENRICH)
def enrich(ctx):
    character = ctx.metadata.get("character")  # Original Character object
    entity_type = ctx.metadata.get("entity_type")  # "character" or "event"
    # ...
```

### Aborting Operations

Set `ctx.abort = True` to stop processing:

```python
@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def prevent_save_without_name(ctx):
    if not ctx.data.canonical_name:
        ctx.abort = True
        print("❌ Cannot save character without name")
    return ctx
```

When aborted:
- No further hooks execute
- The operation raises `StorageError` or returns minimal data
- Original data is unchanged

---

## Priority and Ordering

Hooks execute in **priority order** (lower numbers first):

```python
@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=50)
def validate(ctx):
    # Runs first
    return ctx

@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=100)  # Default priority
def transform(ctx):
    # Runs second
    return ctx

@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=150)
def log(ctx):
    # Runs last
    return ctx
```

### Priority Ranges

Recommended priority conventions:

- **0-49**: Critical operations (validation, auth)
- **50-99**: Data transformation
- **100-149**: Default operations (use 100)
- **150-199**: Logging and monitoring
- **200+**: Cleanup and finalization

---

## Example Hooks

### Auto-Tagging

```python
@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def auto_tag(ctx):
    char = ctx.data

    # Tag all apostles
    if "apostle" in char.roles and "apostle" not in char.tags:
        char.tags.append("apostle")

    # Tag all gospel authors
    if "gospel_author" in char.roles:
        for tag in ["gospel_author", "evangelist"]:
            if tag not in char.tags:
                char.tags.append(tag)

    ctx.data = char
    return ctx
```

### Validation

```python
@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=10)
def validate_character(ctx):
    char = ctx.data
    errors = []

    if not char.canonical_name:
        errors.append("Missing canonical_name")

    if not char.source_profiles:
        errors.append("No source profiles")

    if errors:
        print(f"❌ Validation failed: {', '.join(errors)}")
        ctx.abort = True

    return ctx
```

### Logging

```python
import logging

logger = logging.getLogger("bce.hooks")

@hook(HookPoint.AFTER_CHARACTER_LOAD, priority=200)
def log_load(ctx):
    logger.info(f"Loaded character: {ctx.data.id}")
    return ctx

@hook(HookPoint.AFTER_CHARACTER_SAVE, priority=200)
def log_save(ctx):
    logger.info(f"Saved character: {ctx.data.id}")
    return ctx
```

### Dossier Statistics

```python
@hook(HookPoint.DOSSIER_ENRICH)
def add_statistics(ctx):
    dossier = ctx.data

    if ctx.metadata.get("entity_type") == "character":
        source_count = len(dossier.get("source_ids", []))
        total_traits = sum(
            len(traits)
            for traits in dossier.get("traits_by_source", {}).values()
        )

        dossier["statistics"] = {
            "source_count": source_count,
            "total_traits": total_traits,
            "avg_traits_per_source": total_traits / source_count if source_count > 0 else 0
        }

    ctx.data = dossier
    return ctx
```

### Custom Export Format

```python
import yaml

@hook(HookPoint.EXPORT_FORMAT_RESOLVE)
def add_yaml_export(ctx):
    export_request = ctx.data

    if export_request.get("format") == "yaml":
        dossiers = export_request["dossiers"]
        output = yaml.dump(dossiers, default_flow_style=False)

        export_request["result"] = output
        export_request["handled"] = True

    ctx.data = export_request
    return ctx
```

---

## Plugin Development

### Plugin Structure

A BCE plugin is simply a Python module that registers hooks:

```python
# my_plugin.py
"""
My BCE Plugin

Description of what it does.
"""

from bce.hooks import hook, HookPoint

@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def my_hook(ctx):
    # Hook logic
    return ctx

def setup():
    """Optional setup function"""
    print("Plugin loaded")

# Auto-run on import
setup()
```

### Using Plugins

#### Method 1: Import

```python
# In your code
import my_plugin

# Hooks are now registered
```

#### Method 2: Dynamic Loading

```python
import importlib

# Load plugin by name
plugin = importlib.import_module("my_plugin")
```

### Example Plugin: Auto-Tagger

See `examples/plugins/auto_tag_apostles.py`:

```python
from bce.hooks import hook, HookPoint

@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=50)
def auto_tag_apostles(ctx):
    character = ctx.data

    if "apostle" in character.roles and "apostle" not in character.tags:
        character.tags.append("apostle")
        print(f"✓ Auto-tagged {character.id}")

    ctx.data = character
    return ctx

print("📌 Auto-tagging plugin loaded")
```

### Example Plugin: Dossier Enrichment

See `examples/plugins/dossier_enrichment.py`:

```python
from bce.hooks import hook, HookPoint
from urllib.parse import quote

@hook(HookPoint.DOSSIER_ENRICH, priority=100)
def add_external_links(ctx):
    dossier = ctx.data
    character = ctx.metadata.get("character")

    if character:
        dossier["external_resources"] = {
            "wikipedia": f"https://en.wikipedia.org/wiki/{quote(character.canonical_name)}",
            "bible_gateway": f"https://www.biblegateway.com/quicksearch/?quicksearch={quote(character.canonical_name)}"
        }

    ctx.data = dossier
    return ctx

print("📌 Enrichment plugin loaded")
```

---

## Best Practices

### 1. Keep Hooks Fast

Hooks execute on every operation. Keep logic minimal:

```python
# ❌ BAD - Expensive operation
@hook(HookPoint.AFTER_CHARACTER_LOAD)
def slow_hook(ctx):
    # Don't do this!
    dossier = build_character_dossier(ctx.data.id)  # Expensive!
    return ctx

# ✅ GOOD - Fast operation
@hook(HookPoint.AFTER_CHARACTER_LOAD)
def fast_hook(ctx):
    ctx.data.last_loaded = datetime.now()  # Fast!
    return ctx
```

### 2. Handle Errors Gracefully

Hooks should not crash core functionality:

```python
@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def safe_hook(ctx):
    try:
        # Your logic
        ctx.data = transform(ctx.data)
    except Exception as e:
        # Log but don't crash
        import logging
        logging.error(f"Hook failed: {e}")

    return ctx
```

### 3. Document Your Hooks

```python
@hook(HookPoint.BEFORE_CHARACTER_SAVE, priority=50)
def my_hook(ctx):
    """
    Auto-tag characters based on roles.

    Priority: 50 (runs before default hooks)
    Modifies: ctx.data.tags
    """
    # Implementation
    return ctx
```

### 4. Use Appropriate Priorities

- Use low priority (0-49) for critical operations
- Use default (100) for most hooks
- Use high priority (150+) for logging/monitoring

### 5. Test Your Hooks

```python
def test_my_hook():
    from bce.hooks import HookRegistry, HookPoint, HookContext
    from bce.models import Character

    # Setup
    HookRegistry.clear_all()

    @hook(HookPoint.BEFORE_CHARACTER_SAVE)
    def test_hook(ctx):
        ctx.data.tags.append("test")
        return ctx

    # Test
    char = Character(
        id="test",
        canonical_name="Test",
        aliases=[],
        roles=[],
        tags=[],
        relationships=[],
        source_profiles=[]
    )

    ctx = HookRegistry.trigger(HookPoint.BEFORE_CHARACTER_SAVE, data=char)
    assert "test" in ctx.data.tags

    # Cleanup
    HookRegistry.clear_all()
```

### 6. Avoid Circular Dependencies

Don't trigger operations that could re-trigger your hook:

```python
# ❌ BAD - Can cause infinite loop
@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def bad_hook(ctx):
    from bce import storage
    # Don't do this! It will trigger the same hook again
    storage.save_character(ctx.data)
    return ctx

# ✅ GOOD - Modify data, don't trigger saves
@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def good_hook(ctx):
    ctx.data.tags.append("modified")
    return ctx
```

---

## Performance Considerations

### Hook Overhead

- **When disabled**: Near zero overhead (single boolean check)
- **With no hooks**: Minimal overhead (dictionary lookup)
- **With hooks**: ~0.1-1ms per hook depending on complexity

### Optimization Tips

1. **Disable hooks for batch operations**:
   ```python
   from bce.hooks import HookRegistry

   HookRegistry.disable()
   for char_id in large_list:
       storage.save_character(char)
   HookRegistry.enable()
   ```

2. **Use priority wisely**: Expensive hooks run last (high priority)

3. **Cache computed values**: Don't recompute on every hook call

4. **Abort early**: Set `ctx.abort = True` early to skip remaining hooks

---

## Troubleshooting

### Hooks Not Firing

**Problem**: Your hook isn't being called.

**Solutions**:
1. Check that hook is registered: `HookRegistry.list_handlers()`
2. Verify hooks are enabled: `HookRegistry.is_enabled()`
3. Check the correct hook point is used
4. Ensure the import happens before operations

### Unexpected Behavior

**Problem**: Data is changed unexpectedly.

**Solutions**:
1. List all registered hooks: `HookRegistry.list_handlers()`
2. Check hook priorities
3. Add logging to trace execution
4. Use `HookRegistry.clear_all()` and re-add hooks one at a time

### Performance Issues

**Problem**: Operations are slow with hooks enabled.

**Solutions**:
1. Profile your hooks to find slow ones
2. Move expensive operations to higher priority (run last)
3. Consider disabling hooks for batch operations
4. Cache computed values

### Debugging

Enable hook debugging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("bce.hooks")
logger.setLevel(logging.DEBUG)

# Now all hook triggers will be logged
```

---

## Next Steps

1. **Try the examples**: Run the example plugins in `examples/plugins/`
2. **Write your own**: Create a simple hook for your use case
3. **Share**: Contribute plugins to the community
4. **Explore**: Check out other extensibility features in BCE

---

**Last Updated**: 2025-11-18
**Feedback**: Report issues or suggest improvements via GitHub issues
