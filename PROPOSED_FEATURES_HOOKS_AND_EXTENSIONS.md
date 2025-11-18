# Proposed Features: Hooks, Events, and Extensibility

**Document Date**: 2025-11-18
**Target Phases**: 7-9
**Focus Areas**: Extensibility, Developer Experience, Data Quality Automation

---

## Executive Summary

This proposal introduces a **hooks and events system** to make BCE extensible without modifying core code, along with complementary features for automation, quality assurance, and developer productivity. All proposals maintain BCE's focus as a data and analysis engine, avoiding UI/frontend scope creep.

---

## Priority Tier 1: Core Extensibility (Phase 7)

### 1.1 Hooks and Events System

**Current State**: No extensibility mechanism; all features must be added to core codebase

**Problem**:
- Users can't customize behavior without forking
- No way to add custom validation, processing, or export logic
- Community contributions require core changes
- Testing custom workflows is difficult

**Proposal**: Add a comprehensive hooks and events system

#### Architecture

```python
# bce/hooks.py
from typing import Callable, Any, Dict, List
from dataclasses import dataclass
from enum import Enum

class HookPoint(Enum):
    """Enumeration of all available hook points"""
    # Data lifecycle hooks
    BEFORE_CHARACTER_LOAD = "before_character_load"
    AFTER_CHARACTER_LOAD = "after_character_load"
    BEFORE_CHARACTER_SAVE = "before_character_save"
    AFTER_CHARACTER_SAVE = "after_character_save"
    BEFORE_EVENT_LOAD = "before_event_load"
    AFTER_EVENT_LOAD = "after_event_load"
    BEFORE_EVENT_SAVE = "before_event_save"
    AFTER_EVENT_SAVE = "after_event_save"

    # Validation hooks
    BEFORE_VALIDATION = "before_validation"
    AFTER_VALIDATION = "after_validation"
    VALIDATION_ERROR = "validation_error"

    # Query hooks
    BEFORE_QUERY = "before_query"
    AFTER_QUERY = "after_query"
    CACHE_MISS = "cache_miss"
    CACHE_HIT = "cache_hit"

    # Export hooks
    BEFORE_EXPORT = "before_export"
    AFTER_EXPORT = "after_export"
    EXPORT_FORMAT_RESOLVE = "export_format_resolve"

    # Dossier hooks
    BEFORE_DOSSIER_BUILD = "before_dossier_build"
    AFTER_DOSSIER_BUILD = "after_dossier_build"
    DOSSIER_ENRICH = "dossier_enrich"  # Allows adding custom fields

    # Search hooks
    BEFORE_SEARCH = "before_search"
    AFTER_SEARCH = "after_search"
    SEARCH_RESULT_FILTER = "search_result_filter"
    SEARCH_RESULT_RANK = "search_result_rank"

    # Conflict detection hooks
    BEFORE_CONFLICT_DETECTION = "before_conflict_detection"
    AFTER_CONFLICT_DETECTION = "after_conflict_detection"
    CONFLICT_SEVERITY_SCORE = "conflict_severity_score"

    # System hooks
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    CONFIG_CHANGE = "config_change"

@dataclass
class HookContext:
    """Context object passed to hook handlers"""
    hook_point: HookPoint
    data: Any
    metadata: Dict[str, Any]
    abort: bool = False  # Hook can set this to abort operation

class HookRegistry:
    """Global registry for hook handlers"""

    _handlers: Dict[HookPoint, List[Callable]] = {}
    _enabled: bool = True

    @classmethod
    def register(cls, hook_point: HookPoint, handler: Callable, priority: int = 100):
        """
        Register a hook handler

        Args:
            hook_point: The hook point to register for
            handler: Callable that takes HookContext and returns modified context
            priority: Lower numbers run first (0-999, default 100)
        """
        if hook_point not in cls._handlers:
            cls._handlers[hook_point] = []
        cls._handlers[hook_point].append((priority, handler))
        cls._handlers[hook_point].sort(key=lambda x: x[0])

    @classmethod
    def unregister(cls, hook_point: HookPoint, handler: Callable):
        """Unregister a hook handler"""
        if hook_point in cls._handlers:
            cls._handlers[hook_point] = [
                (p, h) for p, h in cls._handlers[hook_point] if h != handler
            ]

    @classmethod
    def trigger(cls, hook_point: HookPoint, data: Any = None, **metadata) -> HookContext:
        """
        Trigger all handlers for a hook point

        Args:
            hook_point: The hook to trigger
            data: Data to pass to handlers
            **metadata: Additional context metadata

        Returns:
            HookContext with potentially modified data
        """
        if not cls._enabled:
            return HookContext(hook_point, data, metadata)

        context = HookContext(hook_point, data, metadata)

        for priority, handler in cls._handlers.get(hook_point, []):
            try:
                context = handler(context)
                if context.abort:
                    break
            except Exception as e:
                # Log but don't crash
                import logging
                logging.error(f"Hook {hook_point} handler failed: {e}")

        return context

    @classmethod
    def clear_all(cls):
        """Clear all registered hooks (for testing)"""
        cls._handlers = {}

    @classmethod
    def enable(cls):
        """Enable hook system"""
        cls._enabled = True

    @classmethod
    def disable(cls):
        """Disable hook system (for performance)"""
        cls._enabled = False

# Decorator for easy hook registration
def hook(hook_point: HookPoint, priority: int = 100):
    """Decorator to register a function as a hook handler"""
    def decorator(func):
        HookRegistry.register(hook_point, func, priority)
        return func
    return decorator
```

#### Integration into Core Modules

**Example: `bce/storage.py`**

```python
from bce.hooks import HookRegistry, HookPoint

def load_character(char_id: str) -> Character:
    """Load character with hooks"""
    # Before load hook
    ctx = HookRegistry.trigger(
        HookPoint.BEFORE_CHARACTER_LOAD,
        data={"char_id": char_id}
    )

    if ctx.abort:
        raise BceError("Character load aborted by hook")

    # Modify char_id if hook changed it
    char_id = ctx.data.get("char_id", char_id)

    # ... existing load logic ...
    character = _load_character_json(char_id)

    # After load hook (can modify character)
    ctx = HookRegistry.trigger(
        HookPoint.AFTER_CHARACTER_LOAD,
        data=character,
        char_id=char_id
    )

    return ctx.data  # Return potentially modified character
```

**Example: `bce/dossiers.py`**

```python
from bce.hooks import HookRegistry, HookPoint

def build_character_dossier(char_id: str) -> dict:
    """Build dossier with enrichment hooks"""
    # Before build hook
    ctx = HookRegistry.trigger(
        HookPoint.BEFORE_DOSSIER_BUILD,
        data={"char_id": char_id}
    )

    # ... existing dossier build logic ...
    dossier = _build_dossier_dict(character)

    # Enrichment hook (add custom fields)
    ctx = HookRegistry.trigger(
        HookPoint.DOSSIER_ENRICH,
        data=dossier,
        character=character
    )
    dossier = ctx.data

    # After build hook
    ctx = HookRegistry.trigger(
        HookPoint.AFTER_DOSSIER_BUILD,
        data=dossier,
        char_id=char_id
    )

    return ctx.data
```

#### Usage Examples

**Example 1: Auto-tagging on save**

```python
from bce import api
from bce.hooks import hook, HookPoint

@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def auto_tag_apostles(ctx):
    """Automatically tag characters who are apostles"""
    character = ctx.data

    if "apostle" in character.roles and "apostle" not in character.tags:
        character.tags.append("apostle")

    ctx.data = character
    return ctx

# Now all characters with "apostle" role get tagged automatically
jesus = api.get_character("jesus")
# Save triggers the hook
```

**Example 2: Custom validation**

```python
from bce.hooks import hook, HookPoint
from bce.exceptions import ValidationError

@hook(HookPoint.AFTER_VALIDATION)
def require_tags_for_major_characters(ctx):
    """Require major characters to have at least 3 tags"""
    errors = ctx.data  # Validation errors list

    from bce import storage
    for char_id in storage.list_character_ids():
        char = storage.load_character(char_id)
        if "apostle" in char.roles or "gospel_author" in char.roles:
            if len(char.tags) < 3:
                errors.append(
                    f"Character {char_id} is major but has <3 tags"
                )

    ctx.data = errors
    return ctx
```

**Example 3: Export format plugin**

```python
from bce.hooks import hook, HookPoint
import yaml

@hook(HookPoint.EXPORT_FORMAT_RESOLVE)
def add_yaml_export(ctx):
    """Add YAML export format"""
    export_request = ctx.data

    if export_request.get("format") == "yaml":
        dossiers = export_request["dossiers"]
        output_path = export_request.get("output_path")

        yaml_output = yaml.dump(dossiers)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(yaml_output)

        export_request["result"] = yaml_output
        export_request["handled"] = True

    ctx.data = export_request
    return ctx

# Now you can export to YAML
# api.export_all_characters(format="yaml", output_path="chars.yaml")
```

**Example 4: Logging and monitoring**

```python
from bce.hooks import hook, HookPoint
import logging

logger = logging.getLogger("bce.monitoring")

@hook(HookPoint.BEFORE_QUERY, priority=0)  # Run first
def log_query_start(ctx):
    """Log query timing"""
    import time
    ctx.metadata["start_time"] = time.time()
    logger.info(f"Query started: {ctx.data}")
    return ctx

@hook(HookPoint.AFTER_QUERY, priority=999)  # Run last
def log_query_end(ctx):
    """Log query completion"""
    import time
    duration = time.time() - ctx.metadata.get("start_time", 0)
    logger.info(f"Query completed in {duration:.3f}s")
    return ctx
```

**Example 5: Dossier enrichment with external data**

```python
from bce.hooks import hook, HookPoint

@hook(HookPoint.DOSSIER_ENRICH)
def add_external_references(ctx):
    """Add Wikipedia and scholarly links to dossiers"""
    dossier = ctx.data
    character = ctx.metadata.get("character")

    # Add custom section
    dossier["external_resources"] = {
        "wikipedia": f"https://en.wikipedia.org/wiki/{character.canonical_name.replace(' ', '_')}",
        "bible_gateway": f"https://www.biblegateway.com/quicksearch/?quicksearch={character.canonical_name}",
        "scholarly_articles": f"https://scholar.google.com/scholar?q={character.canonical_name}+biblical"
    }

    ctx.data = dossier
    return ctx
```

**Benefits**:
- Zero-modification extensibility
- Community plugins without forking
- Easy testing of custom workflows
- Clear extension points
- Priority-based handler ordering
- Can abort operations if needed

**Estimated Effort**: Medium-High (core integration required)

---

### 1.2 Plugin Architecture

**Current State**: No plugin system

**Proposal**: Formalize plugin discovery and loading

```python
# bce/plugins.py
from pathlib import Path
from typing import List, Optional
import importlib.util

class Plugin:
    """Base class for BCE plugins"""

    name: str = "unnamed_plugin"
    version: str = "0.0.0"
    description: str = ""

    def activate(self):
        """Called when plugin is loaded"""
        pass

    def deactivate(self):
        """Called when plugin is unloaded"""
        pass

class PluginManager:
    """Manages plugin discovery and lifecycle"""

    _loaded_plugins: List[Plugin] = []
    _plugin_dirs: List[Path] = []

    @classmethod
    def add_plugin_directory(cls, path: Path):
        """Add a directory to search for plugins"""
        cls._plugin_dirs.append(path)

    @classmethod
    def discover_plugins(cls) -> List[str]:
        """Find all available plugins"""
        plugins = []
        for plugin_dir in cls._plugin_dirs:
            if not plugin_dir.exists():
                continue
            for file in plugin_dir.glob("*.py"):
                if file.stem != "__init__":
                    plugins.append(file.stem)
        return plugins

    @classmethod
    def load_plugin(cls, plugin_name: str):
        """Load and activate a plugin"""
        for plugin_dir in cls._plugin_dirs:
            plugin_file = plugin_dir / f"{plugin_name}.py"
            if plugin_file.exists():
                spec = importlib.util.spec_from_file_location(
                    plugin_name, plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for Plugin class
                if hasattr(module, "Plugin"):
                    plugin = module.Plugin()
                    plugin.activate()
                    cls._loaded_plugins.append(plugin)
                    return plugin

        raise ValueError(f"Plugin {plugin_name} not found")

    @classmethod
    def unload_plugin(cls, plugin: Plugin):
        """Deactivate and unload a plugin"""
        plugin.deactivate()
        cls._loaded_plugins.remove(plugin)

    @classmethod
    def list_loaded_plugins(cls) -> List[Plugin]:
        """Get list of currently loaded plugins"""
        return cls._loaded_plugins.copy()
```

**Example Plugin**: `~/.bce/plugins/auto_tagger.py`

```python
from bce.plugins import Plugin
from bce.hooks import hook, HookPoint

class Plugin(Plugin):
    name = "auto_tagger"
    version = "1.0.0"
    description = "Automatically tag characters based on roles"

    def activate(self):
        """Register hooks when plugin loads"""
        @hook(HookPoint.BEFORE_CHARACTER_SAVE)
        def auto_tag(ctx):
            character = ctx.data
            # Auto-tag logic
            if "apostle" in character.roles:
                if "apostle" not in character.tags:
                    character.tags.append("apostle")
            ctx.data = character
            return ctx

        self.auto_tag_hook = auto_tag
        print(f"[{self.name}] Activated")

    def deactivate(self):
        """Cleanup when plugin unloads"""
        from bce.hooks import HookRegistry
        HookRegistry.unregister(HookPoint.BEFORE_CHARACTER_SAVE, self.auto_tag_hook)
        print(f"[{self.name}] Deactivated")
```

**CLI Integration**:

```bash
# List available plugins
bce plugins list

# Load a plugin
bce plugins load auto_tagger

# Run command with plugin
bce --plugin auto_tagger character jesus
```

**Benefits**:
- User-space extensions
- No core modifications needed
- Easy distribution via PyPI or Git
- Plugin marketplace potential

**Estimated Effort**: Medium

---

### 1.3 Middleware Pipeline

**Current State**: No request/response processing pipeline

**Proposal**: Add middleware for cross-cutting concerns

```python
# bce/middleware.py
from typing import Callable, Any
from dataclasses import dataclass

@dataclass
class Request:
    """Generic request object"""
    operation: str
    params: dict
    context: dict

@dataclass
class Response:
    """Generic response object"""
    data: Any
    metadata: dict
    errors: list

class Middleware:
    """Base middleware class"""

    def process_request(self, request: Request) -> Request:
        """Process request before operation"""
        return request

    def process_response(self, response: Response) -> Response:
        """Process response after operation"""
        return response

class MiddlewareStack:
    """Manages middleware execution"""

    _middlewares: list = []

    @classmethod
    def add(cls, middleware: Middleware):
        """Add middleware to stack"""
        cls._middlewares.append(middleware)

    @classmethod
    def process(cls, request: Request, operation: Callable) -> Response:
        """Execute middleware pipeline"""
        # Process request through middleware
        for mw in cls._middlewares:
            request = mw.process_request(request)

        # Execute operation
        try:
            result = operation(**request.params)
            response = Response(data=result, metadata={}, errors=[])
        except Exception as e:
            response = Response(data=None, metadata={}, errors=[str(e)])

        # Process response through middleware (reverse order)
        for mw in reversed(cls._middlewares):
            response = mw.process_response(response)

        return response
```

**Example Middleware**:

```python
class LoggingMiddleware(Middleware):
    """Log all operations"""

    def process_request(self, request: Request) -> Request:
        import logging
        logging.info(f"Operation: {request.operation}, Params: {request.params}")
        return request

    def process_response(self, response: Response) -> Response:
        import logging
        if response.errors:
            logging.error(f"Errors: {response.errors}")
        else:
            logging.info(f"Success: {response.data is not None}")
        return response

class CachingMiddleware(Middleware):
    """Cache operation results"""

    cache: dict = {}

    def process_request(self, request: Request) -> Request:
        cache_key = f"{request.operation}:{str(request.params)}"
        if cache_key in self.cache:
            request.context["cached_response"] = self.cache[cache_key]
        return request

    def process_response(self, response: Response) -> Response:
        if "cached_response" in response.metadata:
            return response.metadata["cached_response"]

        cache_key = f"{response.metadata.get('operation')}:{response.metadata.get('params')}"
        self.cache[cache_key] = response
        return response

class AuthorizationMiddleware(Middleware):
    """Check permissions"""

    def process_request(self, request: Request) -> Request:
        # Check if user can perform operation
        if not request.context.get("user_authorized"):
            raise PermissionError("Not authorized")
        return request
```

**Estimated Effort**: Medium

---

## Priority Tier 2: Data Quality Automation (Phase 7)

### 2.1 Automated Data Quality Scoring

**Current State**: Completeness audits exist, but no holistic quality scoring

**Proposal**: Multi-dimensional data quality scoring system

```python
# bce/quality.py
from dataclasses import dataclass
from typing import List, Dict
from bce import api

@dataclass
class QualityScore:
    overall: float  # 0.0-1.0
    dimensions: Dict[str, float]
    recommendations: List[str]
    warnings: List[str]

class QualityScorer:
    """Calculate data quality scores"""

    @staticmethod
    def score_character(char_id: str) -> QualityScore:
        """Score a character's data quality"""
        char = api.get_character(char_id)

        scores = {}
        recommendations = []
        warnings = []

        # Completeness dimension
        scores["completeness"] = QualityScorer._score_completeness(char)
        if scores["completeness"] < 0.7:
            recommendations.append("Add more source profiles or traits")

        # Consistency dimension
        scores["consistency"] = QualityScorer._score_consistency(char)
        if scores["consistency"] < 0.8:
            warnings.append("Potential inconsistencies in trait data")

        # Reference quality dimension
        scores["reference_quality"] = QualityScorer._score_references(char)
        if scores["reference_quality"] < 0.9:
            recommendations.append("Add more specific scripture references")

        # Tag coverage dimension
        scores["tag_coverage"] = QualityScorer._score_tags(char)
        if scores["tag_coverage"] < 0.6:
            recommendations.append("Add relevant thematic tags")

        # Relationship dimension
        scores["relationship_coverage"] = QualityScorer._score_relationships(char)

        # Cross-source dimension
        scores["source_diversity"] = QualityScorer._score_source_diversity(char)
        if scores["source_diversity"] < 0.5:
            recommendations.append("Add profiles from more diverse sources")

        overall = sum(scores.values()) / len(scores)

        return QualityScore(
            overall=overall,
            dimensions=scores,
            recommendations=recommendations,
            warnings=warnings
        )

    @staticmethod
    def _score_completeness(char) -> float:
        """0.0-1.0 based on field completeness"""
        score = 0.0
        max_score = 0.0

        # Has name?
        max_score += 10
        if char.canonical_name:
            score += 10

        # Has aliases?
        max_score += 10
        if char.aliases:
            score += min(len(char.aliases) * 5, 10)

        # Has roles?
        max_score += 15
        if char.roles:
            score += min(len(char.roles) * 5, 15)

        # Has tags?
        max_score += 15
        if char.tags:
            score += min(len(char.tags) * 3, 15)

        # Has source profiles?
        max_score += 30
        if char.source_profiles:
            score += min(len(char.source_profiles) * 10, 30)

        # Source profiles have traits?
        max_score += 20
        total_traits = sum(len(sp.traits) for sp in char.source_profiles)
        score += min(total_traits * 2, 20)

        return score / max_score if max_score > 0 else 0.0

    @staticmethod
    def _score_consistency(char) -> float:
        """Check for internal consistency"""
        # Check if aliases don't conflict with canonical name
        # Check if roles make sense together
        # etc.
        return 1.0  # Placeholder

    @staticmethod
    def _score_references(char) -> float:
        """Quality of scripture references"""
        total_refs = sum(len(sp.references) for sp in char.source_profiles)
        if total_refs == 0:
            return 0.0

        # Check if references are well-formed
        # Check if references are specific vs vague
        return min(total_refs / 10.0, 1.0)

    @staticmethod
    def _score_tags(char) -> float:
        """Tag coverage quality"""
        if not char.tags:
            return 0.0
        return min(len(char.tags) / 5.0, 1.0)

    @staticmethod
    def _score_relationships(char) -> float:
        """Relationship coverage"""
        if not hasattr(char, "relationships") or not char.relationships:
            return 0.0
        return min(len(char.relationships) / 3.0, 1.0)

    @staticmethod
    def _score_source_diversity(char) -> float:
        """Diversity of sources"""
        if not char.source_profiles:
            return 0.0

        unique_sources = len(set(sp.source_id for sp in char.source_profiles))
        # Score higher for more diverse sources (gospels, Paul, Acts, etc.)
        return min(unique_sources / 4.0, 1.0)

# API integration
def get_character_quality_score(char_id: str) -> QualityScore:
    """Get quality score for a character"""
    return QualityScorer.score_character(char_id)

def get_all_quality_scores() -> Dict[str, QualityScore]:
    """Get quality scores for all characters"""
    return {
        char_id: QualityScorer.score_character(char_id)
        for char_id in api.list_character_ids()
    }

def get_low_quality_characters(threshold: float = 0.7) -> List[str]:
    """Find characters below quality threshold"""
    return [
        char_id
        for char_id, score in get_all_quality_scores().items()
        if score.overall < threshold
    ]
```

**CLI Integration**:

```bash
# Check quality score
bce quality character jesus

# Output:
# Overall Score: 0.92
#
# Dimensions:
#   Completeness: 0.95
#   Consistency: 1.00
#   Reference Quality: 0.88
#   Tag Coverage: 0.90
#   Relationship Coverage: 0.85
#   Source Diversity: 1.00
#
# Recommendations:
#   - Add more specific scripture references
```

**Benefits**:
- Objective quality metrics
- Identify data gaps
- Prioritize improvement efforts
- Track quality over time

**Estimated Effort**: Medium

---

### 2.2 Data Changelog and Versioning

**Current State**: No tracking of data changes over time

**Proposal**: Track data changes with git-like versioning

```python
# bce/changelog.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json
from pathlib import Path

@dataclass
class ChangeRecord:
    timestamp: datetime
    entity_type: str  # "character" or "event"
    entity_id: str
    change_type: str  # "create", "update", "delete"
    field_changes: dict  # {"field": {"old": ..., "new": ...}}
    author: Optional[str] = None
    message: Optional[str] = None

class ChangeLog:
    """Track data changes over time"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self._changes: List[ChangeRecord] = []
        self._load()

    def _load(self):
        """Load changelog from file"""
        if self.log_file.exists():
            with open(self.log_file) as f:
                data = json.load(f)
                self._changes = [
                    ChangeRecord(**record) for record in data
                ]

    def _save(self):
        """Save changelog to file"""
        with open(self.log_file, 'w') as f:
            json.dump(
                [self._change_to_dict(c) for c in self._changes],
                f,
                indent=2
            )

    def record_change(self, record: ChangeRecord):
        """Record a change"""
        self._changes.append(record)
        self._save()

    def get_history(self, entity_id: str) -> List[ChangeRecord]:
        """Get full history for an entity"""
        return [c for c in self._changes if c.entity_id == entity_id]

    def get_recent_changes(self, limit: int = 10) -> List[ChangeRecord]:
        """Get most recent changes"""
        return sorted(self._changes, key=lambda c: c.timestamp, reverse=True)[:limit]

    def rollback(self, entity_id: str, to_timestamp: datetime):
        """Rollback entity to a previous state"""
        # Find all changes after timestamp
        # Apply them in reverse
        pass  # TODO: Implement rollback logic

    @staticmethod
    def _change_to_dict(change: ChangeRecord) -> dict:
        """Convert change record to dict"""
        return {
            "timestamp": change.timestamp.isoformat(),
            "entity_type": change.entity_type,
            "entity_id": change.entity_id,
            "change_type": change.change_type,
            "field_changes": change.field_changes,
            "author": change.author,
            "message": change.message
        }

# Integration with storage hooks
from bce.hooks import hook, HookPoint

changelog = ChangeLog(Path("~/.bce/changelog.json").expanduser())

@hook(HookPoint.BEFORE_CHARACTER_SAVE)
def track_character_changes(ctx):
    """Track character changes before save"""
    character = ctx.data
    char_id = ctx.metadata.get("char_id", character.id)

    # Load old version
    try:
        from bce import storage
        old_char = storage.load_character(char_id)
        change_type = "update"

        # Detect field changes
        field_changes = {}
        if old_char.canonical_name != character.canonical_name:
            field_changes["canonical_name"] = {
                "old": old_char.canonical_name,
                "new": character.canonical_name
            }
        # ... check other fields ...

    except:
        change_type = "create"
        field_changes = {"all": "new character"}

    # Record change
    changelog.record_change(ChangeRecord(
        timestamp=datetime.now(),
        entity_type="character",
        entity_id=char_id,
        change_type=change_type,
        field_changes=field_changes
    ))

    return ctx
```

**CLI Integration**:

```bash
# View changelog
bce changelog

# View history for specific character
bce changelog character jesus

# Rollback to previous version
bce rollback character jesus --to "2025-11-01"
```

**Benefits**:
- Track data evolution
- Audit trail
- Rollback capabilities
- Attribution tracking

**Estimated Effort**: Medium

---

### 2.3 Automated Conflict Detection Improvements

**Current State**: Basic conflict detection exists

**Proposal**: Enhanced conflict detection with categorization and severity

```python
# bce/conflicts_enhanced.py
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class ConflictCategory(Enum):
    CHRONOLOGICAL = "chronological"
    GEOGRAPHICAL = "geographical"
    THEOLOGICAL = "theological"
    NARRATIVE = "narrative"
    NUMERICAL = "numerical"
    RELATIONAL = "relational"

class ConflictSeverity(Enum):
    LOW = "low"  # Minor details
    MEDIUM = "medium"  # Significant differences
    HIGH = "high"  # Fundamental contradictions
    CRITICAL = "critical"  # Irreconcilable differences

@dataclass
class EnhancedConflict:
    conflict_id: str
    entity_type: str  # "character" or "event"
    entity_id: str
    field: str
    sources: List[str]
    values: dict  # source_id -> value
    category: ConflictCategory
    severity: ConflictSeverity
    description: str
    implications: List[str]
    scholarly_notes: Optional[str] = None

class EnhancedConflictDetector:
    """Advanced conflict detection"""

    # Severity rules
    SEVERITY_RULES = {
        "resurrection": ConflictSeverity.CRITICAL,
        "divinity": ConflictSeverity.CRITICAL,
        "existence": ConflictSeverity.CRITICAL,
        "date": ConflictSeverity.MEDIUM,
        "location": ConflictSeverity.MEDIUM,
        "wording": ConflictSeverity.LOW,
        "order": ConflictSeverity.MEDIUM,
    }

    # Category detection patterns
    CATEGORY_PATTERNS = {
        ConflictCategory.CHRONOLOGICAL: ["date", "when", "time", "before", "after", "sequence"],
        ConflictCategory.GEOGRAPHICAL: ["location", "where", "place", "city", "region"],
        ConflictCategory.THEOLOGICAL: ["divinity", "nature", "mission", "authority"],
        ConflictCategory.NUMERICAL: ["number", "count", "how many"],
        ConflictCategory.NARRATIVE: ["event", "account", "story", "what happened"],
        ConflictCategory.RELATIONAL: ["relationship", "family", "disciple", "follower"],
    }

    @classmethod
    def detect_conflicts(cls, entity_type: str, entity_id: str) -> List[EnhancedConflict]:
        """Detect all conflicts for an entity"""
        if entity_type == "character":
            return cls._detect_character_conflicts(entity_id)
        elif entity_type == "event":
            return cls._detect_event_conflicts(entity_id)
        return []

    @classmethod
    def _detect_character_conflicts(cls, char_id: str) -> List[EnhancedConflict]:
        """Detect character conflicts with categorization"""
        from bce import api, contradictions

        conflicts = []
        trait_conflicts = contradictions.find_trait_conflicts(char_id)

        for trait, sources_values in trait_conflicts.items():
            conflict = EnhancedConflict(
                conflict_id=f"{char_id}:{trait}",
                entity_type="character",
                entity_id=char_id,
                field=trait,
                sources=list(sources_values.keys()),
                values=sources_values,
                category=cls._categorize_conflict(trait),
                severity=cls._assess_severity(trait, sources_values),
                description=cls._generate_description(trait, sources_values),
                implications=cls._generate_implications(trait, sources_values)
            )
            conflicts.append(conflict)

        return conflicts

    @classmethod
    def _categorize_conflict(cls, field_name: str) -> ConflictCategory:
        """Categorize conflict based on field name"""
        field_lower = field_name.lower()

        for category, patterns in cls.CATEGORY_PATTERNS.items():
            if any(pattern in field_lower for pattern in patterns):
                return category

        return ConflictCategory.NARRATIVE  # Default

    @classmethod
    def _assess_severity(cls, field_name: str, values: dict) -> ConflictSeverity:
        """Assess conflict severity"""
        field_lower = field_name.lower()

        # Check against severity rules
        for keyword, severity in cls.SEVERITY_RULES.items():
            if keyword in field_lower:
                return severity

        # Count how many sources disagree
        unique_values = len(set(values.values()))
        if unique_values == len(values):
            return ConflictSeverity.HIGH  # All sources disagree
        elif unique_values == 2:
            return ConflictSeverity.MEDIUM
        else:
            return ConflictSeverity.LOW

    @classmethod
    def _generate_description(cls, field: str, values: dict) -> str:
        """Generate human-readable description"""
        sources = ", ".join(values.keys())
        return f"Sources {sources} provide different accounts of {field}"

    @classmethod
    def _generate_implications(cls, field: str, values: dict) -> List[str]:
        """Generate implications of the conflict"""
        implications = []

        if "divinity" in field.lower():
            implications.append("Affects christological understanding")
        if "resurrection" in field.lower():
            implications.append("Central to Christian theology")
        if "date" in field.lower() or "when" in field.lower():
            implications.append("Impacts historical reconstruction")

        return implications
```

**API Integration**:

```python
# In bce/api.py
def get_enhanced_conflicts(entity_type: str, entity_id: str) -> List[EnhancedConflict]:
    """Get enhanced conflicts with categorization and severity"""
    from bce.conflicts_enhanced import EnhancedConflictDetector
    return EnhancedConflictDetector.detect_conflicts(entity_type, entity_id)

def get_critical_conflicts() -> List[EnhancedConflict]:
    """Get all critical severity conflicts across all entities"""
    from bce.conflicts_enhanced import EnhancedConflictDetector, ConflictSeverity

    conflicts = []
    for char_id in list_character_ids():
        char_conflicts = EnhancedConflictDetector.detect_conflicts("character", char_id)
        conflicts.extend([c for c in char_conflicts if c.severity == ConflictSeverity.CRITICAL])

    for event_id in list_event_ids():
        event_conflicts = EnhancedConflictDetector.detect_conflicts("event", event_id)
        conflicts.extend([c for c in event_conflicts if c.severity == ConflictSeverity.CRITICAL])

    return conflicts
```

**CLI Integration**:

```bash
# Show conflicts with severity filtering
bce conflicts character jesus --severity critical

# Output:
# CRITICAL CONFLICTS for jesus:
#
# 1. Divinity (theological)
#    Mark: Human messiah
#    John: Pre-existent divine Word
#    Implications:
#      - Affects christological understanding
#      - Central theological difference
#
# 2. Resurrection appearances (narrative)
#    Mark: No appearances (original ending)
#    Matthew: Galilee appearance
#    Luke: Jerusalem appearance
#    John: Multiple appearances
#    Implications:
#      - Central to Christian theology
#      - Affects historical reconstruction
```

**Benefits**:
- Richer conflict analysis
- Prioritize important contradictions
- Better scholarly value
- Categorized for research

**Estimated Effort**: Medium

---

## Priority Tier 3: Developer Experience (Phase 8)

### 3.1 Interactive Data Entry Wizard

**Current State**: Manual JSON editing only

**Proposal**: CLI wizard for guided data entry

```python
# bce/wizard.py
from typing import Optional
import inquirer  # or use built-in input()

class DataEntryWizard:
    """Interactive wizard for data entry"""

    @staticmethod
    def create_character():
        """Guide user through character creation"""
        print("=== Create New Character ===\n")

        # Basic info
        char_id = input("Character ID (lowercase, underscore-separated): ")
        canonical_name = input("Canonical Name: ")

        # Aliases
        aliases = []
        while True:
            alias = input("Alias (or Enter to skip): ")
            if not alias:
                break
            aliases.append(alias)

        # Roles
        roles = []
        while True:
            role = input("Role (or Enter to skip): ")
            if not role:
                break
            roles.append(role)

        # Tags
        tags = []
        while True:
            tag = input("Tag (or Enter to skip): ")
            if not tag:
                break
            tags.append(tag)

        # Source profiles
        source_profiles = []
        while True:
            add_source = input("Add source profile? (y/n): ")
            if add_source.lower() != 'y':
                break

            source_id = input("  Source ID: ")
            traits = {}
            while True:
                trait_key = input("    Trait key (or Enter to skip): ")
                if not trait_key:
                    break
                trait_value = input(f"    {trait_key} value: ")
                traits[trait_key] = trait_value

            references = []
            while True:
                ref = input("    Reference (or Enter to skip): ")
                if not ref:
                    break
                references.append(ref)

            source_profiles.append({
                "source_id": source_id,
                "traits": traits,
                "references": references
            })

        # Build character dict
        character_dict = {
            "id": char_id,
            "canonical_name": canonical_name,
            "aliases": aliases,
            "roles": roles,
            "tags": tags,
            "relationships": [],
            "source_profiles": source_profiles
        }

        # Preview
        import json
        print("\n=== Preview ===")
        print(json.dumps(character_dict, indent=2))

        # Confirm
        confirm = input("\nSave this character? (y/n): ")
        if confirm.lower() == 'y':
            # Save to file
            from bce import storage
            from bce.models import Character, SourceProfile

            char = Character(
                id=character_dict["id"],
                canonical_name=character_dict["canonical_name"],
                aliases=character_dict["aliases"],
                roles=character_dict["roles"],
                tags=character_dict["tags"],
                relationships=character_dict["relationships"],
                source_profiles=[
                    SourceProfile(**sp) for sp in character_dict["source_profiles"]
                ]
            )

            storage.save_character(char)
            print(f"✓ Character '{char_id}' saved!")
        else:
            print("Cancelled.")

    @staticmethod
    def create_event():
        """Guide user through event creation"""
        # Similar structure to create_character
        pass
```

**CLI Integration**:

```bash
# Launch wizard
bce wizard character

# Or shorthand
bce create character
```

**Benefits**:
- Lower barrier to entry
- Guided data entry
- Reduces errors
- Teaches schema structure

**Estimated Effort**: Low-Medium

---

### 3.2 Data Diff and Comparison Tools

**Current State**: No built-in diff tools

**Proposal**: Git-like diff for data changes

```python
# bce/diff.py
from typing import List, Optional
from dataclasses import dataclass
from bce.models import Character, Event

@dataclass
class Diff:
    path: str  # e.g., "traits.divinity" or "source_profiles[0].references[2]"
    old_value: Optional[str]
    new_value: Optional[str]
    change_type: str  # "added", "removed", "modified"

class DataDiff:
    """Compute diffs between data versions"""

    @staticmethod
    def diff_characters(char_a: Character, char_b: Character) -> List[Diff]:
        """Compute diff between two characters"""
        diffs = []

        # Name changes
        if char_a.canonical_name != char_b.canonical_name:
            diffs.append(Diff(
                path="canonical_name",
                old_value=char_a.canonical_name,
                new_value=char_b.canonical_name,
                change_type="modified"
            ))

        # Alias changes
        old_aliases = set(char_a.aliases)
        new_aliases = set(char_b.aliases)

        for alias in new_aliases - old_aliases:
            diffs.append(Diff(
                path=f"aliases",
                old_value=None,
                new_value=alias,
                change_type="added"
            ))

        for alias in old_aliases - new_aliases:
            diffs.append(Diff(
                path=f"aliases",
                old_value=alias,
                new_value=None,
                change_type="removed"
            ))

        # ... similar for other fields ...

        return diffs

    @staticmethod
    def format_diff(diffs: List[Diff]) -> str:
        """Format diff as human-readable text"""
        lines = []
        for diff in diffs:
            if diff.change_type == "added":
                lines.append(f"+ {diff.path}: {diff.new_value}")
            elif diff.change_type == "removed":
                lines.append(f"- {diff.path}: {diff.old_value}")
            elif diff.change_type == "modified":
                lines.append(f"~ {diff.path}:")
                lines.append(f"  - {diff.old_value}")
                lines.append(f"  + {diff.new_value}")

        return "\n".join(lines)
```

**CLI Integration**:

```bash
# Diff two versions
bce diff character jesus --old HEAD~1 --new HEAD

# Show uncommitted changes
bce diff character jesus
```

**Benefits**:
- Track changes clearly
- Review before commit
- Understand data evolution

**Estimated Effort**: Medium

---

### 3.3 Batch Operations CLI

**Current State**: One-at-a-time operations

**Proposal**: Bulk operations support

```bash
# Bulk export
bce export characters --ids jesus,paul,peter --format markdown --output ./exports/

# Bulk validation
bce validate characters --ids jesus,paul,peter

# Bulk quality check
bce quality characters --threshold 0.8 --report quality_report.md

# Bulk tag addition
bce tag add apostle --to peter,paul,andrew,james

# Bulk conflict analysis
bce conflicts --severity high --format csv --output conflicts.csv
```

**Estimated Effort**: Low

---

## Implementation Recommendations

**Phase 7 (Immediate Priority)**:
1. Hooks and Events System (1.1) - Foundation for everything else
2. Plugin Architecture (1.2) - Enables community extensions
3. Automated Quality Scoring (2.1) - Practical value

**Phase 8 (Near-term)**:
1. Enhanced Conflict Detection (2.3) - Scholarly value
2. Data Changelog (2.2) - Audit trail
3. Interactive Wizard (3.1) - Usability

**Phase 9 (Future)**:
1. Middleware Pipeline (1.3) - Advanced use cases
2. Data Diff Tools (3.2) - Developer productivity
3. Batch Operations (3.3) - Efficiency

---

## Success Metrics

For each feature:

1. **Adoption**: Number of users/plugins using the feature
2. **Impact**: Reduction in data quality issues or increase in contributions
3. **Stability**: No breaking changes to existing API
4. **Documentation**: Complete user guide and API reference
5. **Tests**: >80% code coverage for new features

---

## Conclusion

This proposal focuses on **extensibility** and **automation** to make BCE:

- More customizable (hooks, plugins, middleware)
- Higher quality data (automated scoring, conflict enhancement)
- Easier to contribute to (wizard, diff tools, batch ops)

All features maintain BCE's core focus as a data engine and avoid scope creep into UI/frontend territory.

**Next Steps**:
1. Review and prioritize proposals
2. Create GitHub issues for approved features
3. Begin Phase 7 implementation with hooks system
4. Document plugin development guide
5. Build example plugins for common use cases

---

**Document Version**: 1.0
**Status**: Proposal
**Feedback**: Open for discussion
