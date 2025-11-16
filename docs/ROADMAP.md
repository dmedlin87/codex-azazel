# Codex Azazel – Roadmap

Codex Azazel (the `bce` package) is a contradiction-aware Bible character and event engine. Its job is to provide curated, structured, and conflict-aware data about key characters and events, plus clean exports (JSON / Markdown / CLI) for use by other tools. It is **not** a UI, debate engine, or general Bible app.

This roadmap keeps development focused and prevents scope drift.

---

## Phase 0 – Core, Dossiers, Export & Examples (CURRENT)

Goal: Have a working engine with dossiers, exports, CLI, an example script, and basic tests so we can inspect data easily.

**Done:**

- ✅ Core engine (`bce` package with `Character`, `Event`, `SourceProfile`, `EventAccount`, and a queries layer).
- ✅ Data loading for characters/events from JSON (plus core contradiction helpers).
- ✅ Dossier builders:
  - `build_character_dossier(id)`
  - `build_event_dossier(id)`
  - `build_all_character_dossiers()`
  - `build_all_event_dossiers()`
- ✅ Export helpers:
  - JSON exporters for all characters/events.
  - Markdown exporters:
    - `dossier_to_markdown(dossier)`
    - `dossiers_to_markdown(dossiers)`
- ✅ CLI:
  - `python -m bce.cli character <id> --format markdown`
  - `python -m bce.cli event <id> --format markdown`
- ✅ Example script:
  - `examples/print_dossier_markdown.py` builds `jesus` and `crucifixion` dossiers and prints them as Markdown.
- ✅ README “Dossiers & CLI” section documenting programmatic and CLI usage.

**Exit condition for Phase 0:** Core engine + dossiers + export + CLI + example + README + tests are all green. (This condition is met.)

---

## Phase 1 – Data Coverage & Validation

Goal: A small but coherent “v0 canon” of characters and events with no broken references or dangling IDs.

**Planned tasks:**

- Define and document the v0 character set (e.g., Jesus, James, Paul, Peter, Mary, Pilate, John the Baptist, etc.).
- Define and document the v0 event set (e.g., Baptism, Temptation, Temple action, Last Supper, Crucifixion, Empty Tomb, Resurrection appearances, Council of Jerusalem, etc.).
- Add JSON data entries for each v0 character and event, reusing the existing schemas used for `jesus` and `crucifixion`.
- Normalize references:
  - Prefer structured fields like `book`, `chapter`, `verse_start`, `verse_end` (and optionally `translation`) alongside any freeform strings.
- Add validation tests:
  - Iterate all character IDs and assert:
    - Required keys are present (`id`, `label`/`canonical_name`, at least one `source_id`, etc.).
    - All `source_ids` exist in the source profiles.
  - Iterate all event IDs and assert:
    - Required keys are present (e.g., `id`, `label`, `participants`, `accounts`).
    - All participants and source references are consistent.
  - Fail fast on broken or inconsistent data.

**Exit condition for Phase 1:** v0 characters and events exist, and validation tests pass with no dangling IDs or malformed references.

---

## Phase 2 – Thematic Tagging & Query Helpers

Goal: Make it easy to pull all data relevant to a given theme (e.g., apocalypticism, violence, resurrection).

**Planned tasks:**

- Add an optional `tags` field (`list[str]`) to character and event JSON records.
- Implement query helpers (likely in `bce/queries.py` or a new `bce/tags.py`):
  - `list_characters_with_tag(tag: str) -> list[str]`
  - `list_events_with_tag(tag: str) -> list[str]`
- Seed tags for the v0 canon:
  - Examples: `["apocalyptic", "resurrection", "violence", "prophecy", "enochic", "eschatology"]`.
- Add tests to verify tag queries return expected IDs for a few known cases.

**Exit condition for Phase 2:** Tags are available on v0 data and basic tag-based queries are tested and stable.

---

## Phase 3 – Conflict Objects & Ergonomics

Goal: Turn nested conflict structures into explicit “conflict records” that other tools can consume directly.

**Planned tasks:**

- Define a minimal `Conflict` schema, for example:

  ```json
  {
    "id": "jesus:return_timing:mark13_vs_matt24",
    "object_type": "character" | "event",
    "object_id": "jesus",
    "dimension": "return_timing",
    "source_a": "Mark",
    "source_b": "Matthew",
    "value_a": "...",
    "value_b": "...",
    "severity": "low" | "medium" | "high"
  }
  ```

- Implement helpers on top of dossiers:
  - `list_trait_conflicts(character_id) -> list[dict]`
  - `list_account_conflicts(event_id) -> list[dict]`
- Wire these helpers to the existing `trait_conflicts` and `account_conflicts` fields in dossiers.
- Add tests to ensure:
  - For at least one character and event, conflicts list is non-empty.
  - Each conflict record follows the agreed schema.

**Exit condition for Phase 3:** Conflicts can be retrieved as normalized records ready for external tools.

---

## Phase 4 – Stable API Surface for External Tools

Goal: Provide a small, stable API that other systems (TheoEngine, Insight Miner, etc.) can depend on.

**Planned tasks:**

- Add `bce/api.py` exposing a minimal stable surface:
  - `get_character_dossier(id) -> dict`
  - `get_event_dossier(id) -> dict`
  - `list_characters() -> list[str]`
  - `list_events() -> list[str]`
  - `list_conflicts_for_character(id) -> list[dict]`
  - `list_conflicts_for_event(id) -> list[dict]`
- Document schemas in `docs/SCHEMA.md`:
  - Character JSON
  - Event JSON
  - Character dossier
  - Event dossier
  - Conflict record
- Add tests that interact only with `bce.api` (not internal modules) to verify the public contract.

**Exit condition for Phase 4:** External tools can rely on `bce.api` and the documented JSON schemas without touching internals.

---

## Phase 5 – Optional Extensions (Low Priority)

These are explicitly **later** and only if core phases are stable:

- Lightweight HTTP API (e.g., FastAPI) wrapping `bce.api`.
- Additional export formats (HTML, JSON-LD, etc.).
- Scenario scripts, e.g., "dump all apocalyptic conflicts involving Jesus."

---

## Non-goals (to prevent scope drift)

Codex Azazel intentionally does **not** include:

- Frontend/UI or web app.
- Debate engine or apologetics/rebuttal logic.
- General-purpose Bible study app features.
- LLM prompt logic or AI pipelines baked into this repo.

It is a **data and analysis engine** with clean exports, designed to be consumed by other tools.
