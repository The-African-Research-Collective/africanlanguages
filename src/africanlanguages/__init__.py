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
    """Get all available languages"""
    return list(languages.registry.get_all_languages())


def get_language_by_code(code: str) -> Optional[Language]:
    """Get a language by its ISO 639-3 or Glottocode"""
    return languages.registry.get_language(code)


def search_languages(query: str) -> List[Language]:
    """Search languages by name or code"""
    return languages.registry.search(query)


def get_languages_by_country(country: str) -> List[Language]:
    """Get all languages spoken in a specific country"""
    return languages.query().by_country(country).all()


def get_languages_by_region(region: str) -> List[Language]:
    """Get all languages spoken in a specific region"""
    return languages.query().by_region(region).all()


def get_language_count() -> int:
    """Get the total number of languages in the database"""
    return languages.query().count()
