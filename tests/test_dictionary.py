"""Tests for dictionary loader, models, and query functionality"""

import pytest
from pydantic import ValidationError

from africanlanguages.dictionary import Dictionary
from africanlanguages.dictionary.loader import load_dictionary
from africanlanguages.dictionary.models import DictionaryEntry, Translation
from africanlanguages.dictionary.query import DictionaryQuery


# Fixtures
@pytest.fixture
def dictionary():
    """Load dictionary for testing"""
    return load_dictionary(source_lang="yor")


@pytest.fixture
def query(dictionary):
    """Create query interface for testing"""
    return DictionaryQuery(dictionary)


# Model Tests
class TestDictionaryModels:
    """Tests for dictionary models"""

    def test_create_dictionary_entry(self):
        """Test creating a complete dictionary entry"""
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
        assert entry.translations is not None and entry.translations[0].language == "en"

    def test_optional_fields(self):
        """Test creating entry with minimal fields"""
        entry = DictionaryEntry.model_validate({"word": "test", "language": "yor"})
        assert entry.word == "test"
        assert entry.language == "yor"
        assert entry.definition is None

    def test_language_required(self):
        """Test that language field is required"""
        with pytest.raises(ValidationError):
            DictionaryEntry.model_validate({"word": "test", "language": ""})

    def test_language_validation(self):
        """Test language field strips whitespace"""
        entry = DictionaryEntry.model_validate({"word": "test", "language": "  yor  "})
        assert entry.language == "yor"

    def test_translation_language_required(self):
        """Test that Translation language is required"""
        with pytest.raises(ValidationError):
            Translation.model_validate({"text": "hello"})


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
        """Test exact word search"""
        results = query.search("a", fuzzy=False)

        if results:
            assert all(isinstance(r, DictionaryEntry) for r in results)
            assert all(r.word.lower() == "a" for r in results)

    def test_fuzzy_search(self, query):
        """Test fuzzy word search"""
        results = query.search("aba", fuzzy=True, threshold=0.6)
        assert isinstance(results, list)

    def test_get_definitions(self, query):
        """Test definition lookup"""
        definitions = query.get_definitions("a")
        assert isinstance(definitions, list)

    def test_search_edge_cases(self, query):
        """Test search edge cases"""
        assert len(query.search("", fuzzy=False)) == 0
        assert len(query.search("xyzabc123", fuzzy=False)) == 0

    def test_case_insensitive_search(self, query):
        """Test that search is case-insensitive"""
        lower_results = query.search("a", fuzzy=False)
        upper_results = query.search("A", fuzzy=False)
        assert len(lower_results) == len(upper_results)


# Dictionary Class Tests
class TestDictionaryClass:
    """Tests for the Dictionary high-level interface"""

    def test_dictionary_initialization(self):
        """Test creating a Dictionary instance"""
        yoruba_dict = Dictionary("yor")

        assert yoruba_dict.language_code == "yor"
        assert len(yoruba_dict) > 0

    def test_dictionary_search(self):
        """Test Dictionary.search() method"""
        yoruba_dict = Dictionary("yor")
        results = yoruba_dict.search("aga", fuzzy=False)
        assert isinstance(results, list)

    def test_dictionary_define(self):
        """Test Dictionary.define() method"""
        yoruba_dict = Dictionary("yor")
        definitions = yoruba_dict.define("aga")
        assert isinstance(definitions, list)


# Integration Tests
class TestDictionaryIntegration:
    """Integration tests for the complete dictionary workflow"""

    def test_load_search_workflow(self):
        """Test complete workflow: load -> search -> get definitions"""
        dictionary = load_dictionary(source_lang="yor")
        query = DictionaryQuery(dictionary)

        first_word = dictionary[0].word
        results = query.search(first_word, fuzzy=False)
        definitions = query.get_definitions(first_word)

        assert len(results) > 0
        assert isinstance(definitions, list)
