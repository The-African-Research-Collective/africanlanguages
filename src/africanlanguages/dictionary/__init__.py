"""Dictionary module for African language"""

# Use relative imports to avoid circular import during package initialization
from .dictionary import Dictionary
from .loader import DictionaryFields, load_dictionary
from .models import DictionaryEntry, Translation
from .query import DictionaryQuery

__all__ = [
    "Dictionary",
    "DictionaryEntry",
    "DictionaryQuery",
    "DictionaryFields",
    "Translation",
    "load_dictionary",
]
