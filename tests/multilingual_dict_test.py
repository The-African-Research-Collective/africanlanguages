"""Tests for dictionary loader, models, and query functionality"""

import pytest
from pydantic import ValidationError

from africanlanguages.dictionary import Dictionary
from africanlanguages.dictionary.loader import load_dictionary
from africanlanguages.dictionary.models import DictionaryEntry
from africanlanguages.dictionary.query import DictionaryQuery

# Supported language codes (ISO 639-3)
SUPPORTED_LANGUAGES = ["yor", "hau", "swh", "ibo"]


@pytest.mark.parametrize("lang_code", SUPPORTED_LANGUAGES)
class TestMultiLanguageDictionary:
    """
    Parametrized tests for all supported African languages.
    Tests core Dictionary functionalities
    """

    def test_load_dictionary(self, lang_code):
        """Test that dictionary loads and contains DictionaryEntry objects"""
        dictionary = load_dictionary(source_lang=lang_code)

        assert len(dictionary) > 0, f"Dictionary for {lang_code} should not be empty"
        assert all(isinstance(entry, DictionaryEntry) for entry in dictionary)

    def test_dictionary_initialization(self, lang_code):
        """Test Dictionary class initializes correctly"""
        lang_dict = Dictionary(lang_code)

        assert lang_dict.language_code == lang_code
        assert len(lang_dict) > 0

    def test_exact_lookup_first_entry(self, lang_code):
        """Test exact lookup using first dictionary entry"""
        lang_dict = Dictionary(lang_code)
        first_word = lang_dict.entries[0].word

        results = lang_dict.lookup(first_word, exact_match=True)

        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0].word == first_word

    def test_exact_lookup_returns_definition(self, lang_code):
        """Test that exact lookup results have definitions"""
        lang_dict = Dictionary(lang_code)
        first_word = lang_dict.entries[0].word

        results = lang_dict.lookup(first_word, exact_match=True)

        assert len(results) > 0
        assert results[0].definition is not None

    def test_fuzzy_lookup_executes(self, lang_code):
        """Test that fuzzy lookup executes without error"""
        lang_dict = Dictionary(lang_code)
        first_word = lang_dict.entries[0].word

        results = lang_dict.lookup(first_word, exact_match=False, threshold=0.6, top_n=3)

        assert isinstance(results, list)

    def test_lookup_empty_string(self, lang_code):
        """Test that empty string returns no results"""
        lang_dict = Dictionary(lang_code)

        results = lang_dict.lookup("", exact_match=True)

        assert len(results) == 0

    def test_lookup_nonexistent_word(self, lang_code):
        """Test that nonsense word returns no exact matches"""
        lang_dict = Dictionary(lang_code)

        results = lang_dict.lookup("xyzabc123nonsense", exact_match=True)

        assert len(results) == 0

    def test_model_validation_language_required(self, lang_code):
        """Test that DictionaryEntry validates language field"""
        # Valid entry
        valid_entry = DictionaryEntry.model_validate({"word": "test", "language": lang_code})
        assert valid_entry.language == lang_code

        # Invalid entry (empty language)
        with pytest.raises(ValidationError):
            DictionaryEntry.model_validate({"word": "test", "language": ""})

    def test_query_layer_exact_search(self, lang_code):
        """Test DictionaryQuery.find_matches() directly"""
        dictionary = load_dictionary(source_lang=lang_code)
        query = DictionaryQuery(dictionary)

        first_word = dictionary[0].word
        results = query.find_matches(first_word, exact_match=True)

        assert len(results) > 0
        assert results[0].word == first_word

    def test_integration_load_query_search(self, lang_code):
        """Test complete workflow: load → query → search"""
        # Load
        dictionary = load_dictionary(source_lang=lang_code)
        assert len(dictionary) > 0

        # Query
        query = DictionaryQuery(dictionary)
        first_word = dictionary[0].word

        # Search
        results = query.find_matches(first_word, exact_match=True)

        # Verify
        assert len(results) > 0
        assert results[0].word == first_word
        assert results[0].definition is not None
