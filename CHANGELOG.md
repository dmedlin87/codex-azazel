# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to semantic versioning in `pyproject.toml`.

## [0.1.0] - 2025-11-17

### Added

- Core BCE engine with JSON-backed models:
  - `Character`, `SourceProfile`, `Event`, `EventAccount`, `SourceMetadata`.
  - Storage and query helpers for characters and events.
- Dossier builders for characters and events:
  - `bce.dossiers.build_character_dossier` / `build_event_dossier`.
  - `build_all_character_dossiers` / `build_all_event_dossiers`.
- Conflict analysis helpers:
  - Trait comparisons and conflicts for characters.
  - Account conflicts for events.
  - Normalized conflict summaries embedded in dossiers as
    `trait_conflict_summaries` and `account_conflict_summaries`.
- Thematic tagging and search:
  - Optional `tags` on characters and events.
  - Tag helpers and `search_all` for traits, references, accounts, notes, and tags.
- Export helpers:
  - JSON aggregation for all characters/events.
  - Markdown dossier rendering, including relationships and parallels.
  - CSV export for characters and events.
  - BibTeX citation export for sources, characters, and events.
  - Property graph snapshot with characters, events, sources, and relationships.
- High-level public API module `bce.api` exposing a stable surface for:
  - Core objects, dossiers, conflicts, tags, search, exports, and graph snapshots.
- CLI tooling:
  - `bce` entry point for markdown dossiers.
  - `dev_cli.py` for listing, JSON inspection, exports, and data health checks.
- Documentation:
  - README with quickstart examples.
  - `docs/SCHEMA.md` describing core and dossier schemas.
  - `docs/ROADMAP.md` and `docs/features.md` with implementation status.

[0.1.0]: https://github.com/dmedlin87/codex-azazel/releases/tag/v0.1.0
