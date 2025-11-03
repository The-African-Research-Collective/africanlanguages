"""
Main Dictionary class providing a high-level interface.
"""

from typing import List

from africanlanguages.dictionary.loader import load_dictionary
from africanlanguages.dictionary.models import DictionaryEntry
from africanlanguages.dictionary.query import DictionaryQuery


class Dictionary:
    """
    This class provides a convenient way to load and query dictionaries
    without needing to import multiple modules.

    Args:
        language_code: ISO 639-3 language code
        **kwargs: Additional arguments passed to load_dictionary

    """

    def __init__(self, language_code: str, **kwargs):
        """
        Initialize a dictionary for the specified language.

        Args:
            language_code: ISO 639-3 language code
            **kwargs: Additional arguments for load_dictionary
        """
        self.language_code = language_code
        self.entries = load_dictionary(source_lang=language_code, **kwargs)

        # Initialize query interface for searching
        self._query = DictionaryQuery(self.entries)

    def search(self, word: str, fuzzy: bool = False, threshold: float = 0.6) -> List[DictionaryEntry]:
        """
        Search for a word in the dictionary.

        Args:
            word: Word to search for
            fuzzy: Use fuzzy matching (default: False)
            threshold: Minimum similarity for fuzzy matching (0-1)

        Returns:
            List of matching DictionaryEntry objects
        """
        return self._query.search(word, fuzzy=fuzzy, threshold=threshold)

    def define(self, word: str, fuzzy: bool = False) -> List[str]:
        """
        Get definitions for a word.

        Args:
            word: Word to look up
            fuzzy: Use fuzzy matching (default: False)

        Returns:
            List of definition strings
        """
        return self._query.get_definitions(word, fuzzy=fuzzy)

    def __len__(self) -> int:
        """Return the number of entries in the dictionary."""
        return len(self.entries)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Dictionary(language={self.language_code!r}, entries={len(self)})"
