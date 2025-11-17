from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


_BIBLES_ROOT = Path(__file__).resolve().parent / "data" / "bibles" / "EN-English"


def _normalize_book_key(name: str) -> str:
    """Normalize a book name for lookup (case-insensitive, alphanumeric only)."""

    return "".join(ch for ch in name.lower() if ch.isalnum())


@dataclass
class _BibleIndex:
    metadata: Dict[str, Any]
    books: Dict[str, Dict[int, Dict[int, str]]]
    book_keys: Dict[str, str]


_CACHE: Dict[str, _BibleIndex] = {}


def list_translations() -> List[str]:
    """Return available translation codes based on JSON files present."""

    if not _BIBLES_ROOT.exists():
        return []
    return sorted(p.stem for p in _BIBLES_ROOT.glob("*.json") if p.is_file())


def _load_translation(translation: str) -> _BibleIndex:
    if translation in _CACHE:
        return _CACHE[translation]

    path = _BIBLES_ROOT / f"{translation}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Bible JSON file not found for translation {translation!r}: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("metadata", {})
    books: Dict[str, Dict[int, Dict[int, str]]] = {}
    book_keys: Dict[str, str] = {}

    for verse in data.get("verses", []):
        book_name = verse.get("book_name")
        if not book_name:
            continue
        chapter = int(verse.get("chapter", 0))
        verse_num = int(verse.get("verse", 0))
        text = verse.get("text", "")

        if not chapter or not verse_num:
            continue

        books.setdefault(book_name, {}).setdefault(chapter, {})[verse_num] = text

        key = _normalize_book_key(book_name)
        if key not in book_keys:
            book_keys[key] = book_name

    index = _BibleIndex(metadata=metadata, books=books, book_keys=book_keys)
    _CACHE[translation] = index
    return index


def get_translation_metadata(translation: str) -> Dict[str, Any]:
    """Return the metadata block for a translation."""

    index = _load_translation(translation)
    return index.metadata


def get_verse(book: str, chapter: int, verse: int, translation: str = "web") -> str:
    """Return the verse text for the given reference."""

    index = _load_translation(translation)
    key = _normalize_book_key(book)
    canonical = index.book_keys.get(key)
    if canonical is None:
        raise KeyError(f"Unknown book name {book!r} for translation {translation!r}")

    try:
        return index.books[canonical][chapter][verse]
    except KeyError as exc:
        raise KeyError(
            f"Verse not found for {book} {chapter}:{verse} in translation {translation!r}"
        ) from exc


def get_passage(
    book: str,
    chapter: int,
    start_verse: int,
    end_verse: int,
    translation: str = "web",
) -> List[str]:
    """Return a list of verse texts from start_verse to end_verse (inclusive)."""

    if end_verse < start_verse:
        raise ValueError("end_verse must be >= start_verse")
    return [
        get_verse(book, chapter, v, translation=translation)
        for v in range(start_verse, end_verse + 1)
    ]


def get_parallel(
    book: str,
    chapter: int,
    verse: int,
    translations: List[str],
) -> Dict[str, str]:
    """Return a mapping of translation code to verse text for the given reference."""

    result: Dict[str, str] = {}
    for code in translations:
        result[code] = get_verse(book, chapter, verse, translation=code)
    return result
