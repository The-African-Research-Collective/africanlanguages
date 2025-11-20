"""Tests for dictionary loader, models, and query functionality"""

from typing import List

import pytest
from pydantic import ValidationError

from africanlanguages.dictionary import Dictionary
from africanlanguages.dictionary.loader import load_dictionary
from africanlanguages.dictionary.models import DictionaryEntry, Translation
from africanlanguages.dictionary.query import DictionaryQuery


# Fixtures
@pytest.fixture
def dictionary() -> List[DictionaryEntry]:
    """Load dictionary for testing using 'yor' (Yoruba) language code."""
    return load_dictionary(source_lang="yor")


@pytest.fixture
def query(dictionary) -> DictionaryQuery:
    """Create query interface for testing"""
    return DictionaryQuery(dictionary)


# Model Tests
class TestDictionaryModels:
    """Tests for dictionary models using Pydantic validation."""

    def test_create_dictionary_entry(self):
        """Test creating a complete dictionary entry with translations"""
        entry = DictionaryEntry(
            word="adúrà",
            language="yor",
            part_of_speech="noun",
            definition="prayer, supplication, entreaty, petition",
            examples=["Mo gbàdúrà fún ọ."],
            translations=[
                Translation(
                    text="prayer",
                    language="en",
                    context="religious or spiritual supplication",
                )
            ],
        )

        assert entry.word == "adúrà"
        assert entry.language == "yor"
        assert isinstance(entry.language, str)

    def test_optional_fields(self):
        """
        Test creating entry with minimal fields.
        The Pydantic model handles missing optional fields if they have a default (None).
        """
        entry = DictionaryEntry.model_validate({"word": "test", "language": "yor"})
        assert entry.word == "test"
        assert entry.language == "yor"
        assert entry.definition is None
        assert entry.part_of_speech is None
        assert entry.examples == []

    def test_language_required(self):
        """Test that language field is required"""
        with pytest.raises(ValidationError):
            DictionaryEntry.model_validate({"word": "test", "language": ""})

    def test_language_validation(self):
        """
        Test language field strips leading/trailing whitespace during validation.
        This now passes because optional fields are handled correctly in the model.
        """
        entry = DictionaryEntry.model_validate({"word": "test", "language": " yor "})
        assert entry.language == "yor"


# Loader Tests
class TestDictionaryLoader:
    """Tests for dictionary loader"""

    def test_load_dictionary(self):
        """Test loading dictionary with source language"""
        dictionary = load_dictionary(source_lang="yor")

        assert len(dictionary) > 0
        assert isinstance(dictionary[0], DictionaryEntry)
        assert dictionary[0].language == "yor"


# Query Tests
class TestDictionaryQuery:
    """Tests for dictionary query functionality"""

    def test_exact_search(self, query):
        """
        Test exact word search and check definition property.
        """
        results = query.find_matches("aga", exact_match=True)

        assert len(results) > 0
        assert all(isinstance(r, DictionaryEntry) for r in results)
        assert results[0].word == "aga"
        assert results[0].definition is not None

    def test_search_edge_cases(self, query):
        """
        Test search edge cases.
        """
        assert len(query.find_matches("", exact_match=False)) == 0
        assert len(query.find_matches("xyzabc123", exact_match=False)) == 0

    def test_case_insensitive_search(self, query):
        """
        Test that search is case-insensitive.
        Uses word attributes for comparison to avoid TypeError.
        """
        lower_results = query.find_matches("aga", exact_match=False)
        upper_results = query.find_matches("Aga", exact_match=False)
        assert len(lower_results) == len(upper_results)

        lower_words = sorted([r.word for r in lower_results])
        upper_words = sorted([r.word for r in upper_results])
        assert lower_words == upper_words


# Dictionary Class Tests
class TestDictionaryClass:
    """Tests for the Dictionary high-level interface"""

    def test_dictionary_initialization(self):
        """Test creating a Dictionary instance"""
        yoruba_dict = Dictionary("yor")

        assert yoruba_dict.language_code == "yor"
        assert len(yoruba_dict) > 0

    def test_dictionary_search(self):
        """
        Test Dictionary.lookup() method and check definition.
        """
        yoruba_dict = Dictionary("yor")
        results = yoruba_dict.lookup("aga", exact_match=True)
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0].word == "aga"
        assert results[0].definition is not None


# Integration Tests
class TestDictionaryIntegration:
    """Integration tests for the complete dictionary workflow, including new fuzzy logic"""

    def test_load_search_workflow(self):
        """
        Test complete workflow: load -> search -> check definitions.
        """
        dictionary = load_dictionary(source_lang="yor")
        query = DictionaryQuery(dictionary)

        first_word = dictionary[0].word

        # Search the word
        results = query.find_matches(first_word, exact_match=True)

        # Check definitions on the result
        assert len(results) > 0
        assert results[0].word == first_word
        assert results[0].definition is not None

    def test_dictionary_lookup_reverse(self):
        """
        Tests the robust fuzzy logic: searching an English word (definition)
        and expecting the African headword (e.word) to be returned.
        """
        yoruba_dict = Dictionary("yor")

        english_query = "wife"

        # exact_match=False uses the fuzzy dual-purpose search
        results = yoruba_dict.lookup(english_query, exact_match=False, threshold=0.9, top_n=3)

        assert len(results) >= 1

        found_words = {e.word.casefold() for e in results}
        assert "aya" in found_words or "ìyàwó" in found_words

    def test_dictionary_lookup_sentence_reverse_output(self):
        """
        Tests the fix in dictionary.py: simple=True returns e.word when exact_match=False.
        """
        yoruba_dict = Dictionary("yor")

        english_sentence = "my wife"

        # exact_match=False triggers the conditional output path
        results = yoruba_dict.lookup_sentence(english_sentence, exact_match=False, threshold=0.9, simple=True)

        if "wife" in results:
            assert all(isinstance(r, str) for r in results["wife"])
            assert any("aya" in r.casefold() or "ìyàwó" in r.casefold() for r in results["wife"])
        else:
            pytest.fail("The token 'wife' was not found in the sentence results.")

    def test_dictionary_lookup_sentence_exact_forward(self):
        """
        Tests Dictionary.lookup_sentence() for the standard forward lookup output type:
        simple=True and exact_match=True should return the English definition.
        """
        yoruba_dict = Dictionary("yor")

        yoruba_sentence = "Mo wà ní ilé"

        results = yoruba_dict.lookup_sentence(yoruba_sentence, exact_match=True, simple=True)

        if "ilé" in results:
            ile_results = results["ilé"]
            assert all(isinstance(r, str) for r in ile_results)
            assert not any("ilé" in r.casefold() for r in ile_results)
        else:
            pytest.skip("The word 'ilé' was not found in the exact search index.")
