"""
africanlanguages - A comprehensive Python package for African language processing
"""

from typing import List, Optional

from .languages.discovery import LanguageDiscovery
from .languages.models import Language

# Main interfaces
languages = LanguageDiscovery()


# Convenience functions
def get_all_languages() -> List[Language]:
    """
    Get all available languages.

    Returns:
        List[Language]: A list of all languages in the database.
    """
    return list(languages.registry.get_all_languages())


def get_all_language_families() -> List[str]:
    """
    Get all unique language families.

    Returns:
        List[str]: A list of all unique language families.
    """
    families = set()
    for lang in languages.registry.get_all_languages():
        family = lang.family
        if family:
            families.add(family)
    return sorted(families)


def get_language_by_code(code: str) -> Optional[Language]:
    """
    Get a language by its ISO 639-3 or Glottocode.

    Args:
        code: The language code (ISO 639-3 or Glottocode).

    Returns:
        Optional[Language]: The language object if found, None otherwise.
    """
    return languages.registry.get_language(code)


def search_languages(query: str) -> List[Language]:
    """
    Search languages by name or code.

    Args:
        query: The search query string i.e. "yoruba" or "yor".

    Returns:
        List[Language]: A list of languages matching the query.
    """
    return languages.registry.search(query)


def get_languages_by_country(country: str) -> List[Language]:
    """
    Get all languages spoken in a specific country.

    Args:
        country: The country name.

    Returns:
        List[Language]: A list of languages spoken in the specified country.
    """
    return languages.query().by_country(country).all()


def get_languages_by_region(region: str) -> List[Language]:
    """
    Get all languages spoken in a specific region.

    Args:
        region: The region name.

    Returns:
        List[Language]: A list of languages spoken in the specified region.
    """
    return languages.query().by_region(region).all()


def get_language_count() -> int:
    """
    Get the total number of languages in the database.

    Returns:
        int: The total count of languages.
    """
    return languages.query().count()
