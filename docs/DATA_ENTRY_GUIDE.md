# Data Entry Guide

This guide describes how to add or modify characters and events in Codex Azazel's BCE engine while keeping data consistent and useful.

## Where data lives

- Characters: `bce/data/characters/*.json`
- Events: `bce/data/events/*.json`
- Sources (metadata): `bce/data/sources.json`

Schemas for these files are documented in `docs/SCHEMA.md`.

## Adding a new character

1. Pick a stable `id`
   - Use a short, lowercase identifier with underscores if needed, e.g.
     - `mary_magdalene`, `john_baptist`, `barnabas`.
   - Avoid spaces and punctuation.

2. Create `bce/data/characters/<id>.json`
   - Follow the `Character` schema:
     - `id`, `canonical_name`, optional `aliases`, `roles`, `tags`.
     - `source_profiles`: one entry per source (mark, matthew, luke, john, acts, paul_undisputed, etc.).

3. For each `source_profiles` entry
   - Set `source_id` to a known key from `bce/data/sources.json`.
   - Add `traits` as a flat mapping, e.g.
     - `"role": "apostle"`
     - `"orientation": "apocalyptic"`
   - Add `references` as a list of scripture references, e.g.
     - `"Mark 1:9-11"`, `"John 3:22-26"`.
   - Optional `variants`: list of textual variants (see SCHEMA.md).
   - Optional `citations`: list of bibliography keys (e.g. `"Meier 1991:123"`).

4. Optional: relationships
   - Add `relationships` as a list of objects of the form:
     - `{"character_id": "barnabas", "type": "companion", "sources": ["acts"], ...}`
   - Keep `character_id` consistent with existing character IDs.

5. Optional: tags
   - Add `tags` to support thematic search, e.g.
     - `"resurrection"`, `"apocalyptic"`, `"violence"`.

6. Optional: citations
   - Add `citations` at the character level for scholarly references.

7. Run validation and tests
   - `pytest tests/test_validation.py tests/test_data_integrity.py`
   - Fix any reported issues (missing references, unknown sources, etc.).

## Adding a new event

1. Pick a stable `id`
   - Similar rules as characters, e.g. `olivet_discourse`, `empty_tomb`.

2. Create `bce/data/events/<id>.json`
   - Follow the `Event` schema:
     - `id`, `label`, `participants`, `accounts`, optional `parallels`, `tags`.

3. Participants
   - `participants` should be a list of character IDs that already exist (or that you plan to add).

4. Accounts
   - Each account should include:
     - `source_id`: known from `bce/data/sources.json`.
     - `reference`: scripture range (e.g., `"Mark 15:22-37"`).
     - `summary`: short prose summary of the account.
     - Optional `notes`: commentary or important nuances.
     - Optional `variants`: list of textual variants (see SCHEMA.md).

5. Optional: parallels
   - For events with gospel parallels, add a `parallels` list:
     - Each entry:
       - `sources`: list of source IDs.
       - `references`: mapping from source ID to reference string.
       - `relationship`: short string describing the type of parallel, e.g. `"gospel_parallel"`.

6. Optional: tags
   - Add thematic tags similar to characters.

7. Optional: citations
   - Add `citations` at the event level for scholarly references.

8. Optional: textual_variants
   - Add `textual_variants` for major textual variants (see SCHEMA.md for detailed structure).

9. Run validation and tests
   - `pytest tests/test_validation.py tests/test_data_integrity.py`
   - Ensure conflicts and cross-references still pass.

## Updating source metadata

1. Edit `bce/data/sources.json`
   - For each source, you can set:
     - `date_range`, `provenance`, `audience`, `depends_on`.

2. Keep IDs stable
   - Do not change `source_id` values once in use; add new sources instead.

3. Validate
   - Run `pytest tests/test_dossiers.py` to ensure `source_metadata` flows through dossiers.

## Checking your work

- Use `dev_cli.py`:
  - `python dev_cli.py list-chars`
  - `python dev_cli.py show-char <id>`
  - `python dev_cli.py show-event <id>`
  - `python dev_cli.py show-char-dossier <id>`
  - `python dev_cli.py show-event-dossier <id>`
  - `python dev_cli.py check-data`
- Use the main CLI for markdown views:
  - `bce character <id> --format markdown`
  - `bce event <id> --format markdown`

Following this guide plus `docs/SCHEMA.md` and the tests will help keep the dataset consistent, validated, and ready for downstream tools.
