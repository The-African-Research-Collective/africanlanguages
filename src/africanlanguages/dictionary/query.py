"""Query interface for dictionary entries."""

import unicodedata
from difflib import SequenceMatcher
from typing import List

from africanlanguages.dictionary.models import DictionaryEntry


def _norm(s: str) -> str:
    """Normalize text for comparison (NFC + casefold + strip)."""
    if s is None:
        return ""
    text = str(s)
    try:
        return unicodedata.normalize("NFC", text).casefold().strip()
    except Exception:
        return text.casefold().strip()


class DictionaryQuery:
    """Provides search functionality over a list of DictionaryEntry objects."""

    def __init__(self, entries: List[DictionaryEntry]):
        """Initialize the query interface.

        Args:
            entries: List of DictionaryEntry objects to query
        """
        self.entries = entries
        self._build_index()

    def _build_index(self) -> None:
        """Build a simple index for exact word matches."""
        self._word_index = {}
        for entry in self.entries:
            key = _norm(entry.word)
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
        if not word or not word.strip():
            # empty query returns no results
            return []

        word_norm = _norm(word)

        if not fuzzy:
            # return a shallow copy to avoid callers mutating internal state
            return list(self._word_index.get(word_norm, []))

        threshold = max(0.0, min(1.0, float(threshold)))

        results: List[tuple[DictionaryEntry, float]] = []
        for entry in self.entries:
            entry_word = (entry.word or "").lower()
            # compute similarity; short-circuit identical words
            if entry_word == word_norm:
                results.append((entry, 1.0))
                continue
            similarity = SequenceMatcher(None, word_norm, entry_word).ratio()
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
        defs: List[str] = []
        for entry in entries:
            if entry.definition:
                defs.append(entry.definition)
        return defs
