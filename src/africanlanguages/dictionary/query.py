"""Query interface for dictionary entries."""

from difflib import SequenceMatcher
from typing import List

from .models import DictionaryEntry


class DictionaryQuery:
    """
    Provides search functionality over a list of DictionaryEntry objects.
    """

    def __init__(self, entries: List[DictionaryEntry]):
        """
        Initialize the query interface.

        Args:
            entries: List of DictionaryEntry objects to query
        """
        self.entries = entries
        self._build_index()

    def _build_index(self) -> None:
        """Build a simple index for exact word matches."""
        self._word_index = {}
        for entry in self.entries:
            key = entry.word.lower()
            if key not in self._word_index:
                self._word_index[key] = []
            self._word_index[key].append(entry)

    def search(self, word: str, fuzzy: bool = False, threshold: float = 0.6) -> List[DictionaryEntry]:
        """
        Search for entries matching a word.

        Args:
            word: Word to search for
            fuzzy: Use fuzzy matching
            threshold: Minimum similarity for fuzzy matching (0-1)

        Returns:
            List of matching DictionaryEntry objects
        """
        word_lower = word.lower()

        if not fuzzy:
            return self._word_index.get(word_lower, [])

        results = []
        for entry in self.entries:
            similarity = SequenceMatcher(None, word_lower, entry.word.lower()).ratio()
            if similarity >= threshold:
                results.append((entry, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results]

    def get_definitions(self, word: str, fuzzy: bool = False) -> List[str]:
        """
        Get definitions for a word.
        Args:
            word: Word to look up
            fuzzy: Use fuzzy matching

        Returns:
            List of definition strings, in the same order as the dataset
        """
        entries = self.search(word, fuzzy=fuzzy)
        if not entries:
            return []
        return [entry.definition for entry in entries if entry.definition]
