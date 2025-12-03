"""
Main Dictionary class providing a high-level interface.
"""

from typing import Any, Dict, List

from africanlanguages.dictionary.loader import load_dictionary
from africanlanguages.dictionary.models import DictionaryEntry
from africanlanguages.dictionary.query import DictionaryQuery
from africanlanguages.dictionary.utils import strip_punctuation_edges


class Dictionary:
    def __init__(self, language_code: str, **kwargs):
        self.language_code = language_code
        self.entries = load_dictionary(source_lang=language_code, **kwargs)
        self._query = DictionaryQuery(self.entries)

    def lookup(
        self, word: str, exact_match: bool = True, top_n: int = 2, threshold: float = 0.6
    ) -> List[DictionaryEntry]:
        """
        Search for a single word in the dictionary.

        Args:
            word (str): The word or token to search for.
            exact_match (bool): If True, only returns exact matches found
                                via the index. If False, performs a fuzzy search
                                using SequenceMatcher. Defaults to True.
            top_n (int): The maximum number of results to return during a
                        fuzzy search. Defaults to 2.
            threshold (float): The minimum similarity score (0.0 to 1.0)
                            required for a result in a fuzzy search.
                            Defaults to 0.6.

        Returns:
            List[DictionaryEntry]: A list of matching dictionary entries, sorted by relevance (score).
        """

        clean_word = strip_punctuation_edges(word)
        return self._query.find_matches(clean_word, exact_match=exact_match, top_n=top_n, threshold=threshold)

    def lookup_sentence(
        self, sentence: str, exact_match: bool = True, top_n: int = 2, threshold: float = 0.6, simple: bool = True
    ) -> Dict[str, Any]:
        """
        Search for every word (token) in a sentence.

        Args:
            sentence (str): The input text to tokenize and search.
            exact_match (bool): If True, performs exact lookups for each token.
                                If False, performs fuzzy lookups (useful for
                                reverse lookup/translation). Defaults to True.
            top_n (int): The maximum number of results per token during a
                        fuzzy search. Defaults to 2.
            threshold (float): The minimum similarity score (0.0 to 1.0)  required for a fuzzy match.
                                Defaults to 0.6.
            simple (bool): If True, the results dictionary contains a simplified
                        list of strings (definitions for forward lookup,
                        headwords for reverse lookup). If False, returns
                        full DictionaryEntry objects. Defaults to True.

        Returns:
            Dict[str, Any]: A dictionary where keys are the original tokens
                            from the sentence, and values are the matching
                            results (either List[str] or List[DictionaryEntry]).
        """

        raw_tokens = sentence.split()
        results = {}

        for token in raw_tokens:
            query_term = strip_punctuation_edges(token)

            if not query_term:
                continue

            entries = self._query.find_matches(query_term, exact_match=exact_match, top_n=top_n, threshold=threshold)

            if simple:
                if exact_match:
                    simplified_results = [e.definition for e in entries if e.definition]
                else:
                    simplified_results = [e.word for e in entries]

                results[token] = simplified_results
            else:
                results[token] = entries

        return results

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"Dictionary(language={self.language_code!r}, entries={len(self)})"
