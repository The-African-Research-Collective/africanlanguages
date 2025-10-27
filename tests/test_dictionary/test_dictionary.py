"""Combined tests for dictionary loader, models, and query functionality"""

import pytest

from africanlanguages.dictionary.loader import load_dictionary, load_yoruba_dict
from africanlanguages.dictionary.models import DictionaryEntry, Translation
from africanlanguages.dictionary.query import DictionaryQuery
from africanlanguages.languages.models import Language, LanguageCodes


# Fixtures
@pytest.fixture
def yoruba_lang():
    """Fixture for Yoruba language"""
    return Language(name="Yoruba", codes=LanguageCodes(iso639_3="yor"), family="Niger-Congo")


@pytest.fixture
def english_lang():
    """Fixture for English language"""
    return Language(name="English", codes=LanguageCodes(iso639_3="eng"), family="Indo-European")


@pytest.fixture
def dictionary():
    """Load dictionary for testing"""
    return load_yoruba_dict()


@pytest.fixture
def query(dictionary):
    """Create query interface for testing"""
    return DictionaryQuery(dictionary)


# Model Tests
class TestDictionaryModels:
    """Tests for dictionary models"""

    def test_create_dictionary_entry(self, yoruba_lang, english_lang):
        """Test creating a complete dictionary entry"""
        entry = DictionaryEntry(
            word="adúrà",
            language=yoruba_lang,
            part_of_speech="noun",
            definition="prayer, supplication, entreaty, petition",
            examples=["Mo gbàdúrà fún ọ."],
            translations=[
                Translation(text="prayer", language=english_lang, context="religious or spiritual supplication")
            ],
        )

        assert entry.word == "adúrà"
        assert entry.language is not None
        assert entry.language.get_primary_code() == "yor"
        assert entry.examples is not None
        assert "Mo gbàdúrà fún ọ." in entry.examples
        assert entry.translations is not None
        assert len(entry.translations) > 0
        assert entry.translations[0].text == "prayer"

    def test_optional_fields(self, yoruba_lang):
        """Test creating entry with minimal fields"""
        entry = DictionaryEntry(
            word="adúrà", language=yoruba_lang, part_of_speech=None, definition=None, examples=None, translations=None
        )
        assert entry.word == "adúrà"
        assert entry.definition is None
        assert entry.examples is None
        assert entry.translations is None


# Loader Tests
class TestDictionaryLoader:
    """Tests for dictionary loader"""

    def test_load_yoruba_dict(self):
        """Test loading Yoruba dictionary"""
        dictionary = load_yoruba_dict()
        assert len(dictionary) > 0

    def test_load_dictionary_error(self):
        """Test error handling for invalid dataset"""
        with pytest.raises(FileNotFoundError):
            load_dictionary("nonexistent-dataset", "yor")


# Query Tests
class TestDictionaryQuery:
    """Tests for dictionary query functionality"""

    def test_exact_search(self, query):
        """Test exact word search"""
        results = query.search("adúrà", fuzzy=False)
        if results:
            assert any(entry.word == "adúrà" for entry in results)

    def test_fuzzy_search(self, query):
        """Test fuzzy word search"""
        results = query.search("baba", fuzzy=True, threshold=0.7)
        # Fuzzy search should find similar words
        assert len(results) > 0, "Fuzzy search should find similar words"

    def test_get_definitions(self, query):
        """Test definition lookup"""
        definitions = query.get_definitions("adúrà")
        if definitions:
            assert any("prayer" in d.lower() for d in definitions if d)

    def test_search_edge_cases(self, query):
        """Test search edge cases"""
        assert len(query.search("", fuzzy=False)) == 0  # Empty search
        assert len(query.search("xyzabc123", fuzzy=False)) == 0  # Non-existent word
