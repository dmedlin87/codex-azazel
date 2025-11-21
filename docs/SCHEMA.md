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

### 1.2 TextualVariant

**NEW in this release.** Backed by `bce.models.TextualVariant` and embedded in SourceProfile or EventAccount.

A structured representation of textual variants across manuscript families (MT, LXX, DSS, etc.).

**Required fields:**

- `manuscript_family: str` – Manuscript tradition identifier (e.g., `"MT"`, `"LXX"`, `"4QSamuel-a"`, `"P46"`, `"Codex Sinaiticus"`)
- `reading: str` – The specific text or value in this manuscript tradition
- `significance: str` – Why this variant matters for interpretation

**Example:**

```json
{
  "manuscript_family": "LXX",
  "reading": "sons of God",
  "significance": "Alters Deuteronomy 32:8 to reflect divine council imagery instead of ethnic boundaries"
}
```

### 1.3 SourceProfile

Backed by `bce.models.SourceProfile` and embedded in character JSON.

**Required fields:**

- `source_id: str` – e.g. `"mark"`, `"matthew"`, `"luke"`, `"john"`, `"paul_undisputed"`, `"acts"`.
- `traits: dict[str, str]` – narrative/theological features keyed by trait name (see §1.3.1 for standard vocabulary).
- `references: list[str]` – scripture references.

**Optional fields:**

- `variants: list[TextualVariant]` – **NEW**: Textual variants relevant to this source profile (default: `[]`)
- `citations: list[str]` – **NEW**: Bibliography keys linking to scholarly citations (default: `[]`)

#### 1.3.1 Standard Trait Keys Vocabulary

**NEW in this release.** The `bce.models.STANDARD_TRAIT_KEYS` constant defines a controlled vocabulary for trait keys to maintain consistency across source profiles. The validation system will warn (but not error) when trait keys fall outside this vocabulary.

**Categories include:**

- **Core theological**: `christology`, `eschatology`, `soteriology`, `pneumatology`, `ecclesiology`
- **Mission and ministry**: `mission_focus`, `teaching_emphasis`, `ministry_location`, `ministry_duration`, `ministry_recipients`
- **Miracles**: `miracles`, `signs`, `healings`, `exorcisms`, `nature_miracles`
- **Conflict**: `conflicts`, `opponents`, `trial_details`, `accusations`
- **Death and resurrection**: `death_resurrection`, `passion_narrative`, `crucifixion_details`, `resurrection_details`, `post_resurrection_appearances`
- **Torah and law**: `torah_stance`, `halakha_interpretation`, `purity_laws`, `sabbath_observance`, `temple_attitude`
- **Identity**: `messianic_claims`, `divine_sonship`, `prophetic_identity`, `authority_claims`
- **Relationships**: `discipleship_model`, `family_relations`, `gender_inclusivity`, `social_justice`
- **Literary features**: `parables`, `apocalyptic_discourse`, `wisdom_sayings`, `pronouncement_stories`, `controversy_stories`
- **Context**: `jewish_context`, `greco_roman_context`, `political_stance`, `economic_teaching`
- **Character**: `portrayal`, `character_development`, `emotions`, `virtues`, `vices`
- **Eschatological themes**: `kingdom_of_god`, `future_hope`, `judgment_themes`, `imminent_expectation`, `realized_eschatology`
- **Spirit and supernatural**: `spirit_activity`, `angelic_encounters`, `demonic_opposition`, `visions`, `revelations`
- **Community and ethics**: `ethical_teaching`, `community_formation`, `ritual_practices`, `prayer_life`, `table_fellowship`

**Usage:** While not enforced, using standard keys improves data consistency and queryability. Custom trait keys are allowed but will generate validation warnings.

### 1.4 Event

Backed by `bce.models.Event` and JSON files in `bce/data/events/*.json`.

**Required fields:**

- `id: str` – Unique identifier
- `label: str` – Display name

**Optional fields:**

- `participants: list[str]` – character IDs (default: `[]`)
- `accounts: list[EventAccount]` – per-source event accounts (default: `[]`)
- `parallels: list[dict]` – normalized parallel-pericope records (e.g. gospel parallels) (default: `[]`)
- `tags: list[str]` – topical tags (e.g. `"resurrection"`, `"empty_tomb"`) (default: `[]`)
- `citations: list[str]` – **NEW**: Bibliography keys linking to scholarly citations (default: `[]`)
- `textual_variants: list[dict]` – **NEW**: Major textual variants (default: `[]`)

**Textual Variant structure (Event):**

The `textual_variants` list on an Event object uses a more detailed schema than the `TextualVariant` model used in accounts:

- `source_id: str`
- `reference: str`
- `variant_type: str` – e.g. `"addition"`, `"omission"`, `"alteration"`
- `description: str`
- `manuscript_support: str`
- `manuscript_lack: str`
- `significance: str`

### 1.5 EventAccount

Backed by `bce.models.EventAccount` and embedded in event JSON.

**Required fields:**

- `source_id: str` – Source identifier
- `reference: str` – Scripture range
- `summary: str` – Account summary

**Optional fields:**

- `notes: str | null` – Free-form notes (default: `null`)
- `variants: list[TextualVariant]` – **NEW**: Textual variants in this account (default: `[]`)

### 1.6 SourceMetadata

Loaded from `bce/data/sources.json` via `bce.sources.load_source_metadata` and surfaced in dossiers.

**Required fields:**

- `source_id: str`

**Optional fields:**

- `date_range: str | null` – Dating range (e.g., `"70-75 CE"`)
- `provenance: str | null` – Geographic origin (e.g., `"Rome"`, `"Antioch"`)
- `audience: str | null` – Intended audience (e.g., `"Gentile Christians"`)
- `depends_on: list[str]` – Other sources this one likely depends on (default: `[]`)

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
- `variants_by_source: dict[str, list[dict]]` – **NEW**: `source_id -> list[TextualVariant]` (serialized as dicts)
- `citations_by_source: dict[str, list[str]]` – **NEW**: `source_id -> list[citation_key]`
- `trait_comparison: dict[str, dict[str, str]]` – full trait comparison across sources (`trait -> source_id -> value`).
- `trait_conflicts: dict[str, dict[str, str]]` – only traits with differing non-empty values.
- `trait_conflict_summaries: dict[str, dict]` - normalized conflict metadata per trait (see §3), enriched with claim taxonomy and harmonization hints.
- `claim_graph: {"claims": list[dict], "conflicts": list[dict]}` - flattened claim records plus detected claim conflicts with `claim_type`, `conflict_type`, `severity`, and suggested harmonization moves.
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
- `account_conflict_summaries: dict[str, dict]` - normalized conflict metadata per field (see §3), enriched with claim taxonomy and harmonization hints.
- `claim_graph: {"claims": list[dict], "conflicts": list[dict]}` - flattened claim records plus detected account-level claim conflicts with harmonization hints.
- `parallels: list[dict]` – normalized parallels copied from `Event.parallels`.
- `citations: list[str]` – **NEW**: Bibliography keys for this event
- `textual_variants: list[dict]` – **NEW**: Major textual variants (list of dicts)

### 2.3 EventAccountDossier

Backed by `bce.dossier_types.EventAccountDossier`.

Fields:

- `source_id: str`
- `reference: str`
- `summary: str`
- `notes: str | null`
- `variants: list[dict]` – **NEW**: List of TextualVariant objects (serialized as dicts)

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
  "claim_type": "chronology" | "theology" | "geography" | "narrative" | "identity" | "textual",
  "conflict_type": "chronology_sequence" | "chronology_dating" | "narrative_emphasis" | ...,
  "sources": {
    "mark": "none",
    "matthew": "birth in Bethlehem with magi",
    "luke": "census and manger"
  },
  "distinct_values": ["none", "birth in Bethlehem with magi", "census and manger"],
  "harmonization_moves": [{"move": "anchor_by_range", "description": "Use a shared range that covers divergent dates"}],
  "dominant_value": "birth in Bethlehem with magi",
  "notes": "3 distinct value(s) across 3 source(s)",
  "rationale": "3 distinct value(s) across 3 source(s); type=chronology_sequence"
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
