# AI Features Quick Reference

**Full context**: [AI_FEATURES_PROPOSAL.md](./AI_FEATURES_PROPOSAL.md)

## Engine Reframe: Claim Graph With Hooks

- BCE is a claim graph engine with strongly typed core models (characters, events, relationships, claims).
- Storage is pluggable: JSON today; database/graph backends later.
- Hooks wrap the canonical integration points (storage, validation, search, dossiers, export).
- Dossier and export schemas are the stable, versioned API surface.

## Phase A: Core Hardening (Schema, Relationships, Traits)

- Add `bce.schema` as the gate between raw JSON and `bce.models` (Pydantic or TypedDict + explicit checks).
- Run schema validation inside `storage.load_character/load_event` and `validation.validate_all()`.
- Replace `relationships: List[dict]` with a typed `Relationship` model:
  `source_id`, `target_id`, `type` (enum), `attestation` (source_ids + refs), optional `strength/notes`; validate cross-refs and allowed types.
- Split traits into `structured_traits` (controlled vocabulary using `STANDARD_TRAIT_KEYS`, enum/bool/number where possible) and `trait_notes` (prose). Unknown or untyped keys become errors, not warnings.
- Dossiers expose a `relationships_by_type`/`relationship_graph` section built from the new model.

## Phase B: Claim Graph Layer

- Introduce a `Claim` model: `subject_id`, `predicate`, `object` (typed value or target id), `source_id`, `reference`, optional `variant_id`, `confidence`, `note`.
- Build the claim set during `build_character_dossier` / `build_event_dossier` (or a shared `build_claim_graph()` that dossiers call).
- Run contradiction detection over claims: conflicting `(subject, predicate)` with incompatible objects and attestation metadata.
- Apply a stable claim-type taxonomy (`chronology`, `theology`, `geography`, `narrative`, `identity`, `textual`) and expose conflict_type + minimal harmonization hints alongside conflict summaries/dossiers.
- Graph exports become straightforward: nodes = entities; relationships/traits/events = typed claims/edges.

## Phase C: Storage Abstraction and Indexing

- Define a `StorageBackend` protocol/ABC with `list_character_ids`, `get_character_raw`, `save_character_raw`, plus event analogs.
- Refactor `bce.storage.StorageManager` to delegate to a backend instance: start with `JsonStorageBackend`; keep room for `SqliteStorageBackend` or `GraphStorageBackend`.
- Build lightweight in-memory indexes on load (or on demand) for characters (roles/tags/source) and events (participants/location). Optionally persist `_index.json` to skip recomputation.
- `search_all` first hits indexes for pre-filtering, then falls back to full scans.

## Phase D: Hooks and Plugins

- Hook points: BEFORE/AFTER_CHARACTER_LOAD/SAVE, BEFORE/AFTER_EVENT_LOAD/SAVE, BEFORE_VALIDATION/AFTER_VALIDATION, BEFORE_SEARCH/SEARCH_RESULT_FILTER/SEARCH_RESULT_RANK/AFTER_SEARCH, BEFORE_DOSSIER_BUILD/DOSSIER_ENRICH/AFTER_DOSSIER_BUILD, BEFORE_EXPORT/EXPORT_FORMAT_RESOLVE/AFTER_EXPORT.
- Plugins ride these hooks for storage side-effects (indexing/changelog), validation extensions, search ranking/filters, dossier enrichment, and export format additions.
- AI lives behind plugins: embedding ranking at `SEARCH_RESULT_RANK`, LLM summaries at `DOSSIER_ENRICH`, validation suggestions via `AFTER_VALIDATION`.
- Enable hook execution with `BCE_ENABLE_HOOKS=true` and opt-in to specific AI behaviors using `BCE_AI_PLUGINS` (e.g., `search_ranking`, `tag_suggestions`, `role_sanity`).

## Semantic Workflows & Explainers

- `/api/ai/semantic`: returns a compiled `plan` (Scopes, clauses, hints, field weights) plus the top semantic matches so the UI can show why a query hit specific traits/events.
- `/api/ai/qa`: contrastive question answering that surfaces `answers`, a `contrast_set`, and an `explanation` block with `what_if` toggles; hooks can augment explanations (e.g., role sanity notes).
- Frontend widgets consume the plan + explanation to render guided workflows, explanation cards, and toggles that trigger broader or tighter plan variants.

## Stable, Versioned Dossier and Export API

- Treat dossier/output schemas as the public contract; include `schema_version` (e.g., `"1.0"`) in every dossier.
- Maintain a dossier schema doc + changelog; exports flow through hooks so new formats (Obsidian, LaTeX tables, RDF) stay out of core.

## Short Roadmap (Pragmatic)

1) Lock core: add `bce.schema` gate, enforce typed `Relationship`, split traits into structured vs prose, make validation strict.  
2) Claim graph: implement `Claim`, build graph during dossier construction, refactor contradictions to operate on claims.  
3) Storage/index: introduce `StorageBackend`, keep JSON as default, add in-memory (optional persisted) indexes feeding search.  
4) Hooks/plugins: ship hook skeleton, move AI and advanced exports into plugins wired at the integration points.

**Status**: Planning/in design to align core with claim graph + hook architecture. Implementation details live in `AI_FEATURES_PROPOSAL.md`; this page is the quick navigation aid.

## Curation Workflow Automator (New)

- **Review Queue**: `api.build_curation_review_queue(entity_type="character"|"event", limit=10)` blends completeness gaps, conflict density, and semantic uncertainty into a prioritized list.
- **Cluster Guardian**: `api.run_cluster_guardian(num_clusters=6, support_threshold=0.6)` surfaces cluster-level tag/role inconsistencies with alignment suggestions.
- **Diff Impact**: `api.summarize_json_edit_impact(before, after, entity_type="character")` explains how JSON edits change completeness and conflict metrics.
- **CLI**: `python -m bce.curation_cli queue --entity character --limit 5`, `... guardian --clusters 5`, `... diff before.json after.json --entity event`.
