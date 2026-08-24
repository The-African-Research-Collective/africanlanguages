"""In-memory lookup over audited dictionary entries."""

import re
import unicodedata
from difflib import SequenceMatcher

from africanlanguages.dictionary.models import DictionaryEntry

_HYPHENS = re.compile(
    r"[\-\u058a\u05be\u1400\u1806\u2010-\u2015\u2e17\u2e1a\u2e3a-\u2e3b\u2e40\u301c\u3030\u30a0\ufe31-\ufe32\ufe58\ufe63\uff0d]+"
)


def normalize_text(text: str, *, separator_insensitive: bool = False) -> str:
    """Normalize Unicode, case, whitespace, and optionally hyphen-like separators."""
    value = unicodedata.normalize("NFC", str(text or "")).casefold().strip()
    if separator_insensitive:
        value = _HYPHENS.sub(" ", value)
    return " ".join(value.split())


def _fuzzy_text(text: str, *, separator_insensitive: bool) -> str:
    normalized = normalize_text(text, separator_insensitive=separator_insensitive)
    return "".join(
        character for character in unicodedata.normalize("NFD", normalized) if not unicodedata.combining(character)
    )


class DictionaryQuery:
    """Exact, prefix, and fuzzy lookup over a list of entries."""

    def __init__(self, entries: list[DictionaryEntry]):
        self.entries = entries
        self._word_index: dict[str, list[DictionaryEntry]] = {}
        self._loose_index: dict[str, list[DictionaryEntry]] = {}
        for entry in entries:
            self._word_index.setdefault(normalize_text(entry.word), []).append(entry)
            self._loose_index.setdefault(normalize_text(entry.word, separator_insensitive=True), []).append(entry)

    def search(
        self,
        word: str,
        fuzzy: bool = False,
        threshold: float = 0.6,
        *,
        normalization_aware: bool = True,
        prefix: bool = False,
        limit: int | None = None,
    ) -> list[DictionaryEntry]:
        """Search for exact, prefix, or fuzzy headword matches."""
        if not word or not word.strip() or (limit is not None and limit <= 0):
            return []
        strict_key = normalize_text(word)
        loose_key = normalize_text(word, separator_insensitive=True)

        if prefix:
            index = self._loose_index if normalization_aware else self._word_index
            key = loose_key if normalization_aware else strict_key
            results = [entry for candidate, values in index.items() if candidate.startswith(key) for entry in values]
            results.sort(key=lambda entry: (normalize_text(entry.word), entry.entry_id or ""))
            return results[:limit] if limit is not None else results

        if not fuzzy:
            results = list(self._word_index.get(strict_key, []))
            if not results and normalization_aware:
                results = list(self._loose_index.get(loose_key, []))
            return results[:limit] if limit is not None else results

        threshold = max(0.0, min(1.0, float(threshold)))
        query_key = _fuzzy_text(word, separator_insensitive=normalization_aware)
        scored: list[tuple[DictionaryEntry, float]] = []
        for entry in self.entries:
            candidate = _fuzzy_text(entry.word, separator_insensitive=normalization_aware)
            similarity = SequenceMatcher(None, query_key, candidate).ratio()
            if similarity >= threshold:
                scored.append((entry, similarity))
        scored.sort(key=lambda item: (-item[1], normalize_text(item[0].word), item[0].entry_id or ""))
        results = [entry for entry, _ in scored]
        return results[:limit] if limit is not None else results

    def prefix(self, value: str, limit: int = 20) -> list[DictionaryEntry]:
        """Return normalization-aware prefix matches."""
        return self.search(value, prefix=True, limit=limit)

    def lookup_many(self, words: list[str]) -> dict[str, list[DictionaryEntry]]:
        """Look up multiple headwords while preserving the caller's keys."""
        return {word: self.search(word) for word in words}

    def get_definitions(self, word: str, fuzzy: bool = False) -> list[str]:
        """Return non-empty definitions for matching entries."""
        return [entry.definition for entry in self.search(word, fuzzy=fuzzy) if entry.definition]
