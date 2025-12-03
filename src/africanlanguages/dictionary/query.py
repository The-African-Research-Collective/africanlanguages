"""Query interface for dictionary entries."""

from collections import defaultdict
from difflib import SequenceMatcher
from typing import Dict, List

from africanlanguages.dictionary.models import DictionaryEntry, Translation
from africanlanguages.dictionary.utils import normalize_text


class DictionaryQuery:
    """Provides search functionality over a list of DictionaryEntry objects."""

    def __init__(self, entries: List[DictionaryEntry]):
        self.entries = entries
        self._index: Dict[str, List[DictionaryEntry]] = defaultdict(list)
        self._build_index()

    def _build_index(self):
        """
        Builds the index for fast exact lookups (Headwords and definitions).
        """
        for entry in self.entries:
            head = normalize_text(entry.word)
            self._index[head].append(entry)

            if entry.definition and len(entry.definition.split()) < 5:
                def_key = normalize_text(entry.definition)
                current_list = self._index[def_key]
                if entry not in current_list:
                    current_list.append(entry)

            for t in entry.translations:
                t_str = t.text if isinstance(t, Translation) else str(t)
                t_key = normalize_text(t_str)

                current_list = self._index[t_key]
                if entry not in current_list:
                    current_list.append(entry)

    def find_matches(
        self, token: str, exact_match: bool = True, top_n: int = 2, threshold: float = 0.6
    ) -> List[DictionaryEntry]:
        """
        Core search logic. Attempts exact match first, then falls back
        to fuzzy search if enabled.

        The fuzzy search checks the headword and definition
        fields to support both forward and reverse lookups.
        """

        token_norm = normalize_text(token)
        if not token_norm:
            return []

        if token_norm in self._index:
            match_list = self._index[token_norm]

            # Prioritizes entry whose original word exactly matches the search token.
            primary_match = next((e for e in match_list if e.word == token), None)

            if primary_match:
                sorted_list = [primary_match] + [e for e in match_list if e != primary_match]
                return sorted_list

            return match_list

        if exact_match:
            return []

        # Fuzzy Search (Fallback)
        scored = []
        for entry in self.entries:
            max_score = 0.0

            head_norm = normalize_text(entry.word)
            if abs(len(head_norm) - len(token_norm)) <= 4:
                score = SequenceMatcher(None, token_norm, head_norm).ratio()
                max_score = max(max_score, score)

            for t in entry.translations:
                t_str = t.text if isinstance(t, Translation) else str(t)
                t_norm = normalize_text(t_str)

                if token_norm in t_norm:
                    max_score = max(max_score, 1.0)
                else:
                    if abs(len(t_norm) - len(token_norm)) < 15:
                        score = SequenceMatcher(None, token_norm, t_norm).ratio()
                        max_score = max(max_score, score)

            if entry.definition:
                def_norm = normalize_text(entry.definition)

                if token_norm in def_norm:
                    max_score = max(max_score, 1.0)
                else:
                    if abs(len(def_norm) - len(token_norm)) < 15:
                        score = SequenceMatcher(None, token_norm, def_norm).ratio()
                        max_score = max(max_score, score)

            if max_score >= threshold:
                scored.append((entry, max_score))

        scored.sort(key=lambda x: (x[1], -len(x[0].word)), reverse=True)
        return [entry for entry, _ in scored[:top_n]]
