from typing import List, Optional, Callable, Dict, Any
from .models import Language
from .registry import LanguageRegistry

class LanguageQuery:
    """Fluent query interface for language discovery"""

    def __init__(self, registry: LanguageRegistry):
        self.registry = registry
        self._filters: List[Callable[[Language], bool]] = []
        self._results: Optional[List[Language]] = None

    def by_country(self, country: str) -> 'LanguageQuery':
        """Filter by country"""
        self._filters.append(lambda lang: lang.in_country(country))
        return self

    def by_region(self, region: str) -> 'LanguageQuery':
        """Filter by region"""
        self._filters.append(lambda lang: region in lang.geographic.regions)
        return self

    def with_speakers_above(self, count: int) -> 'LanguageQuery':
        """Filter by minimum speaker count"""
        def filter_func(lang):
            return (lang.demographic.speaker_count or 0) >= count
        self._filters.append(filter_func)
        return self

    def all(self) -> List[Language]:
        """Execute query and return all results"""
        if self._results is None:
            self._results = self._execute()
        return self._results

    def first(self) -> Optional[Language]:
        """Get first result"""
        results = self.all()
        return results[0] if results else None

    def count(self) -> int:
        """Get count of results"""
        return len(self.all())

    def _execute(self) -> List[Language]:
        """Execute all filters and return results"""
        results = []
        for language in self.registry.get_all_languages():
            if all(f(language) for f in self._filters):
                results.append(language)
        return results

class LanguageDiscovery:
    """Main interface for language discovery"""

    def __init__(self, registry: Optional[LanguageRegistry] = None):
        self.registry = registry or LanguageRegistry()

    def query(self) -> LanguageQuery:
        """Start a new query"""
        return LanguageQuery(self.registry)

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about languages"""
        return {}

    def random_language(self, **filters) -> Optional[Language]:
        """Get a random language matching filters"""
        pass
