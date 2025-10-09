from typing import Callable, List, Optional

from .models import Language
from .registry import LanguageRegistry


class LanguageQuery:
    """Fluent query interface for language discovery"""

    def __init__(self, registry: LanguageRegistry):
        """
        Initialize the language query.

        Args:
            registry: The language registry to query.
        """
        self.registry = registry
        self._filters: List[Callable[[Language], bool]] = []
        self._results: Optional[List[Language]] = None

    def by_country(self, country: str) -> "LanguageQuery":
        """
        Filter by country.

        Args:
            country: The country name to filter by.

        Returns:
            LanguageQuery: Self for method chaining.
        """
        self._filters.append(lambda lang: lang.in_country(country))
        return self

    def by_region(self, region: str) -> "LanguageQuery":
        """
        Filter by region.

        Args:
            region: The region name to filter by.

        Returns:
            LanguageQuery: Self for method chaining.
        """
        self._filters.append(lambda lang: region in lang.geographic.regions)
        return self

    def with_speakers_above(self, count: int) -> "LanguageQuery":
        """
        Filter by minimum speaker count.

        Args:
            count: Minimum number of speakers.

        Returns:
            LanguageQuery: Self for method chaining.
        """

        def filter_func(lang):
            """
            Filter function for speaker count.

            Args:
                lang: The language to check.

            Returns:
                bool: True if speaker count meets the threshold.
            """
            return (lang.demographic.speaker_count or 0) >= count

        self._filters.append(filter_func)
        return self

    def all(self) -> List[Language]:
        """
        Execute query and return all results.

        Returns:
            List[Language]: All languages matching the query filters.
        """
        if self._results is None:
            self._results = self._execute()
        return self._results

    def first(self) -> Optional[Language]:
        """
        Get first result.

        Returns:
            Optional[Language]: The first language matching the query, or None.
        """
        results = self.all()
        return results[0] if results else None

    def count(self) -> int:
        """
        Get count of results.

        Returns:
            int: Number of languages matching the query.
        """
        return len(self.all())

    def _execute(self) -> List[Language]:
        """
        Execute all filters and return results.

        Returns:
            List[Language]: Languages that pass all filters.
        """
        results = []
        for language in self.registry.get_all_languages():
            if all(f(language) for f in self._filters):
                results.append(language)
        return results


class LanguageDiscovery:
    """Main interface for language discovery"""

    def __init__(self, registry: Optional[LanguageRegistry] = None):
        """
        Initialize the language discovery interface.

        Args:
            registry: Optional language registry. Creates default if not provided.
        """
        self.registry = registry or LanguageRegistry()

    def query(self) -> LanguageQuery:
        """
        Start a new query.

        Returns:
            LanguageQuery: A new query instance.
        """
        return LanguageQuery(self.registry)
