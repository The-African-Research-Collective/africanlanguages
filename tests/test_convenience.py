import pytest

from africanlanguages import (
    get_all_languages,
    get_language_by_code,
    get_language_count,
    get_languages_by_region,
    search_languages,
)
from africanlanguages.languages.models import Language


class TestConvenienceFunctions:
    """Test suite for convenience functions in __init__.py"""

    def test_get_all_languages_returns_list_of_languages(self):
        """Test that get_all_languages returns a list of Language objects"""
        languages = get_all_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0  # Should have some languages loaded

        # Check that all items are Language instances
        for lang in languages:
            assert isinstance(lang, Language)

    @pytest.mark.parametrize(
        "iso_code,expected_name",
        [
            ("yor", "Yoruba"),
            ("ibo", "Igbo"),
            ("zul", "Zulu"),
        ],
    )
    def test_get_language_by_code_with_valid_iso_code(self, iso_code, expected_name):
        """Test getting a language by valid ISO 639-3 code"""
        language = get_language_by_code(iso_code)
        assert language is not None
        assert isinstance(language, Language)
        assert language.name == expected_name
        assert language.codes.iso639_3 == iso_code

    @pytest.mark.parametrize("glotto_lang_code,lang_name", [("yoru1245", "Yoruba"), ("pula1262", "Pular")])
    def test_get_language_by_code_with_valid_glottocode(self, glotto_lang_code, lang_name):
        """Test getting a language by valid Glottocode"""
        # Test with Yoruba's glottocode
        language = get_language_by_code(glotto_lang_code)

        assert language is not None
        assert isinstance(language, Language)
        assert language.name == lang_name
        assert language.codes.glottocode == glotto_lang_code

    def test_get_language_by_code_with_invalid_code(self):
        """Test getting a language by invalid code returns None"""
        language = get_language_by_code("invalid_code_123")

        assert language is None

    def test_search_languages_by_name(self):
        """Test searching languages by name"""
        results = search_languages("Yoruba")

        assert isinstance(results, list)
        assert len(results) >= 1

        # Should find Yoruba
        yoruba_found = any(lang.name == "Yoruba" for lang in results)
        assert yoruba_found

    def test_search_languages_by_code(self):
        """Test searching languages by code"""
        results = search_languages("yoru1245")

        assert isinstance(results, list)
        assert len(results) >= 1

        # Should find Yoruba by its Glottocode
        yoruba_found = any(lang.codes.iso639_3 == "yor" for lang in results)
        assert yoruba_found

    def test_search_languages_with_no_results(self):
        """Test searching with a query that returns no results"""
        results = search_languages("nonexistent_language_xyz")

        assert isinstance(results, list)
        assert len(results) == 0

    def test_get_languages_by_region(self):
        """Test getting languages by region"""
        results = get_languages_by_region("Africa")

        assert isinstance(results, list)
        assert len(results) > 0  # Africa region should have languages

        for lang in results:
            assert isinstance(lang, Language)
            assert "Africa" in lang.geographic.regions

    def test_get_languages_by_invalid_region(self):
        """Test getting languages by invalid region"""
        results = get_languages_by_region("InvalidRegion")

        assert isinstance(results, list)
        assert len(results) == 0

    def test_get_language_count(self):
        """Test getting the total language count"""
        count = get_language_count()

        assert isinstance(count, int)
        assert count > 0  # Should have some languages

        # Verify count matches get_all_languages length
        all_languages = get_all_languages()
        assert count == len(all_languages)

    def test_convenience_functions_consistency(self):
        """Test that convenience functions are consistent with each other"""
        all_languages = get_all_languages()
        count = get_language_count()

        assert len(all_languages) == count

        # Test that searching for a specific language works
        if all_languages:
            first_lang = all_languages[0]
            primary_code = first_lang.get_primary_code()

            if primary_code:
                found_by_code = get_language_by_code(primary_code)
                assert found_by_code is not None
                assert found_by_code.name == first_lang.name
