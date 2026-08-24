"""Dictionary module for African language"""

# Use relative imports to avoid circular import during package initialization
from .dictionary import Dictionary
from .loader import AFRI_DICT_REVISION, DictionaryFields, available_dictionaries, load_dictionary
from .models import DictionaryAvailability, DictionaryEntry, DictionaryMetadata, Translation, UsageExample
from .providers import (
    AfriDictProvider,
    DelimitedFileProvider,
    DictionaryProvider,
    FreeDictProvider,
    WiktextractProvider,
)
from .query import DictionaryQuery, normalize_text

__all__ = [
    "AFRI_DICT_REVISION",
    "Dictionary",
    "DictionaryAvailability",
    "DictionaryEntry",
    "DictionaryMetadata",
    "DictionaryQuery",
    "DictionaryFields",
    "DictionaryProvider",
    "AfriDictProvider",
    "DelimitedFileProvider",
    "FreeDictProvider",
    "WiktextractProvider",
    "Translation",
    "UsageExample",
    "available_dictionaries",
    "load_dictionary",
    "normalize_text",
]
