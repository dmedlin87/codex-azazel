from __future__ import annotations

from typing import Dict

import bce.bibles as bibles


class TestBibleTranslations:
    def test_list_translations_includes_expected(self) -> None:
        translations = bibles.list_translations()

        assert "web" in translations
        assert "asvs" in translations
        assert "kjv" in translations
        assert "kjv_strongs" in translations

    def test_get_verse_from_web_and_asvs(self) -> None:
        web_text = bibles.get_verse("Genesis", 1, 1, translation="web")
        asvs_text = bibles.get_verse("Genesis", 1, 1, translation="asvs")

        assert "In the beginning" in web_text
        assert web_text
        assert asvs_text
        assert web_text != asvs_text


class TestBibleHelpers:
    def test_get_passage_returns_multiple_verses(self) -> None:
        passage = bibles.get_passage("Genesis", 1, 1, 3, translation="web")

        assert isinstance(passage, list)
        assert len(passage) == 3
        assert all(isinstance(v, str) and v for v in passage)

    def test_get_parallel_returns_text_for_each_translation(self) -> None:
        translations = ["web", "asvs", "kjv"]
        verses: Dict[str, str] = bibles.get_parallel(
            "Genesis", 1, 1, translations=translations
        )

        assert set(verses.keys()) == set(translations)
        for code, text in verses.items():
            assert isinstance(text, str)
            assert text
