"""
Utility functions for text normalization and cleaning.
"""

import unicodedata

import regex


def normalize_text(text: str) -> str:
    """
    Standardize text for lookup: NFC normalization, casefold, strip whitespace.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    return text.casefold().strip()


def strip_punctuation_edges(text: str) -> str:
    """
    Removes punctuation ONLY from the start and end of a token.
    """
    if not text:
        return ""

    return regex.sub(r"(^\p{P}+)|(\p{P}+$)", "", text)
