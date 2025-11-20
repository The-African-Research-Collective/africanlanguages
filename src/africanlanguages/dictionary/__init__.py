"""Dictionary module for African languages"""

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
