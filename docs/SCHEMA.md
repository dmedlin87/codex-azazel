# BCE Schema

This document describes the main JSON/data shapes exposed by the BCE (Biblical Character Engine) library. It is intended as a stable reference for API consumers.

## 1. Core models

### 1.1 Character

Backed by `bce.models.Character` and JSON files in `bce/data/characters/*.json`.

**Required fields:**

- `id: str` – Unique identifier in `snake_case`, must match filename (without `.json`)
- `canonical_name: str` – Display name (e.g., `"Jesus of Nazareth"`, `"Paul the Apostle"`)
- `aliases: list[str]` – Alternative names and titles
- `roles: list[str]` – Roles/occupations (e.g., `"apostle"`, `"prophet"`, `"teacher"`)
- `source_profiles: list[SourceProfile]` – At least one source profile required

**Optional fields:**

- `tags: list[str]` – Topical tags for thematic queries (e.g., `"jesus"`, `"resurrection"`, `"apocalyptic"`)
- `relationships: list[dict]` – Relationship records to other characters (see below)

**Relationship structure (enforced):**

Each relationship must be a dict with the following **required fields**:

- `character_id: str` – Target character ID (must reference an existing character)
- `type: str` – Relationship type (e.g., `"mother"`, `"brother"`, `"inner_circle_disciple"`)
- `sources: list[str]` – Source IDs where this relationship appears (e.g., `["mark", "matthew", "luke"]`)
- `references: list[str]` – Scripture references for this relationship (e.g., `["Mark 3:31-35", "John 19:25-27"]`)

**Optional relationship fields:**

- `notes: str` – Additional context or notes about the relationship

**Example relationship:**

```json
{
  "character_id": "peter",
  "type": "inner_circle_disciple",
  "sources": ["mark", "matthew", "luke", "john", "acts"],
  "references": ["Mark 8:27-33", "Matthew 16:13-20", "Luke 5:1-11"],
  "notes": "Confesses Jesus as messiah yet misunderstands suffering path."
}
```

**⚠️ Breaking change from earlier versions:**

The legacy nested format (grouping relationships by category like `{"family": [...], "disciples": [...]}`) is **no longer supported** and will raise a `StorageError`. All relationships must use the flat list format with `character_id` references.

### 1.2 SourceProfile

Backed by `bce.models.SourceProfile` and embedded in character JSON.

Fields:

- `source_id: str` – e.g. `"mark"`, `"matthew"`, `"luke"`, `"john"`, `"paul_undisputed"`, `"acts"`.
- `traits: dict[str, str]` – narrative/theological features keyed by trait name.
- `references: list[str]` – scripture references.

### 1.3 Event

Backed by `bce.models.Event` and JSON files in `bce/data/events/*.json`.

Fields:

- `id: str`
- `label: str`
- `participants: list[str]` – character IDs.
- `accounts: list[EventAccount]`
- `parallels: list[dict]` – normalized parallel-pericope records (e.g. gospel parallels).
- `tags: list[str]` – optional topical tags (e.g. `"resurrection"`, `"empty_tomb"`).

### 1.4 EventAccount

Backed by `bce.models.EventAccount` and embedded in event JSON.

Fields:

- `source_id: str`
- `reference: str` – scripture range.
- `summary: str`
- `notes: str | null` – optional free-form notes.

### 1.5 SourceMetadata

Loaded from `bce/data/sources.json` via `bce.sources.load_source_metadata` and surfaced in dossiers.

Fields:

- `source_id: str`
- `date_range: str | null`
- `provenance: str | null`
- `audience: str | null`
- `depends_on: list[str]` – other sources this one likely depends on.

## 2. Dossier schemas

Dossiers are JSON-friendly summaries built from the core models.

### 2.1 CharacterDossier

Backed by `bce.dossier_types.CharacterDossier` and produced by `bce.dossiers.build_character_dossier` or `bce.api.build_character_dossier`.

Fields (keys are stable):

- `id: str`
- `canonical_name: str`
- `aliases: list[str]`
- `roles: list[str]`
- `source_ids: list[str]` – unique source IDs seen in `source_profiles`.
- `source_metadata: dict[str, dict[str, str]]` – maps `source_id` to metadata fields (`date_range`, `provenance`, `audience`, `depends_on`).
- `traits_by_source: dict[str, dict[str, str]]` – `source_id -> trait_name -> trait_value`.
- `references_by_source: dict[str, list[str]]` – `source_id -> list[reference]`.
- `trait_comparison: dict[str, dict[str, str]]` – full trait comparison across sources (`trait -> source_id -> value`).
- `trait_conflicts: dict[str, dict[str, str]]` – only traits with differing non-empty values.
- `trait_conflict_summaries: dict[str, dict]` – normalized conflict metadata per trait (see §3).
- `relationships: list[dict]` – relationship records as stored on the underlying `Character`.
- `parallels: list[dict]` – reserved for future use; currently an empty list.

### 2.2 EventDossier

Backed by `bce.dossier_types.EventDossier` and produced by `bce.dossiers.build_event_dossier` or `bce.api.build_event_dossier`.

Fields:

- `id: str`
- `label: str`
- `participants: list[str]` – character IDs.
- `accounts: list[EventAccountDossier]` – normalized account records (see below).
- `account_conflicts: dict[str, dict[str, str]]` – differing values across accounts (`field_name -> source_id -> value`).
- `account_conflict_summaries: dict[str, dict]` – normalized conflict metadata per field (see §3).
- `parallels: list[dict]` – normalized parallels copied from `Event.parallels`.

### 2.3 EventAccountDossier

Backed by `bce.dossier_types.EventAccountDossier`.

Fields:

- `source_id: str`
- `reference: str`
- `summary: str`
- `notes: str | null`

## 3. Conflict summary schema

Conflict summaries are normalized records produced by:

- `bce.contradictions.summarize_character_conflicts(char_id)`
- `bce.contradictions.summarize_event_conflicts(event_id)`
- And embedded in dossiers under `trait_conflict_summaries` and `account_conflict_summaries`.

Each entry in these mappings has the form:

```json
{
  "field": "birth_narrative",
  "severity": "low" | "medium" | "high",
  "category": "narrative" | "chronology" | "theology" | "geography" | "other",
  "sources": {
    "mark": "none",
    "matthew": "birth in Bethlehem with magi",
    "luke": "census and manger"
  },
  "distinct_values": ["none", "birth in Bethlehem with magi", "census and manger"],
  "notes": "3 distinct value(s) across 3 source(s)"
}
```

The surrounding mapping is:

- For characters: `trait_name -> summary_record`.
- For events: `field_name -> summary_record` (fields like `"summary"`, `"notes"`, `"reference"`).

## 4. Search result schema

The `bce.search.search_all` and `bce.api.search_all` functions return a list of JSON-serializable dicts describing where a query matched.

Each result has at least:

- `type: "character" | "event"`
- `id: str` – character or event ID.
- `match_in: str` – one of:
  - `"traits"`
  - `"references"`
  - `"accounts"`
  - `"notes"`
  - `"tags"`

Additional fields depend on `match_in`:

- For `match_in == "traits"`:
  - `source_id: str`
  - `field: str` – trait name.
  - `value: str` – trait value.

- For `match_in == "references"`:
  - `source_id: str`
  - `reference: str`

- For `match_in == "accounts"`:
  - `source_id: str`
  - `reference: str | null`
  - `summary: str | null`

- For `match_in == "notes"`:
  - `source_id: str`
  - `reference: str | null`
  - `notes: str`

- For `match_in == "tags"`:
  - `tag: str` – the tag value that matched.

## 5. Tags and tag helpers

Characters and events can define a `tags: list[str]` field in their JSON records.

The following helpers expose tag-based lookup:

- `bce.api.list_characters_with_tag(tag: str) -> list[str]`
- `bce.api.list_events_with_tag(tag: str) -> list[str]`

Matching is case-insensitive; tags are compared by lowercased value.

## 6. Stability and compatibility

- The keys documented above (for core models, dossiers, conflict summaries, and search results) are considered stable.
- New keys may be added over time in a backward-compatible way.
- Field *values* (especially free-text summaries and notes) are descriptive and may change as data is enriched, but their types will remain as documented here.
