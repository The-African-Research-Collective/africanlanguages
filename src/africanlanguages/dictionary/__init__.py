# Convenience imports
from .loader import load_dictionary, load_yoruba_dict
from .models import DictionaryEntry, Translation
from .query import DictionaryQuery

__all__ = [
    "DictionaryQuery",
    "load_dictionary",
    "load_yoruba_dict",
    "DictionaryEntry",
    "Translation",
]
