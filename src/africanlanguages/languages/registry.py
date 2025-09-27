import json
from typing import Dict, Iterator, List, Optional, Set

from ..core.base import Singleton
from ..core.config import ConfigManager
from ..core.exceptions import DataLoadError
from .models import Language


class LanguageRegistry(metaclass=Singleton):
    """Central registry for all languages"""

    def __init__(self):
        """
        Initialize the language registry.
        """
        self._languages: Dict[str, Language] = {}
        self._indexes: Dict[str, Dict[str, Set[str]]] = {}
        self._loaded = False

    def _load_data(self) -> None:
        """
        Load language data from JSON file.
        """
        if self._loaded:
            return

        path = ConfigManager().config.data_paths.languages_db

        if not path.exists():
            raise DataLoadError(f"Language data file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                language = self._create_language_from_json(item)
                if language:
                    primary_code = language.get_primary_code()
                    if primary_code:
                        self._languages[primary_code] = language

            self._build_indexes()
            self._loaded = True

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in language data file: {e}") from e
        except Exception as e:
            raise DataLoadError(f"Failed to load language data: {e}") from e

    def _create_language_from_json(self, item: dict) -> Optional[Language]:
        """
        Create Language object from JSON item.

        Args:
            item: Dictionary containing language data from JSON.

        Returns:
            Optional[Language]: Language object if valid, None otherwise.
        """
        try:
            from .models import GeographicInfo, LanguageCodes

            name = item.get("name")
            if not name:
                return None

            codes = LanguageCodes(iso639_3=item.get("iso639_3"), glottocode=item.get("glottocode"))

            coordinates = None
            if "latitude" in item and "longitude" in item:
                coordinates = {"lat": item["latitude"], "lng": item["longitude"]}

            geographic = GeographicInfo(regions=[item.get("macro_area", "Africa")], coordinates=coordinates)

            metadata = {"family": item.get("family")}

            return Language(name=name, codes=codes, geographic=geographic, metadata=metadata)

        except Exception:
            return None

    def get_language(self, code: str) -> Optional[Language]:
        """
        Get language by any valid code.

        Args:
            code: The language code to search for.

        Returns:
            Optional[Language]: The language if found, None otherwise.
        """
        if not self._loaded:
            self._load_data()

        # Try direct lookup first
        if code in self._languages:
            return self._languages[code]

        # Search in indexes
        if "codes" in self._indexes:
            for lang_code in self._indexes["codes"].get(code, set()):
                return self._languages.get(lang_code)

        return None

    def _build_indexes(self) -> None:
        """
        Build search indexes for fast queries.
        """
        self._indexes = {"codes": {}, "names": {}}

        for lang_code, language in self._languages.items():
            # Index codes
            if language.codes.iso639_3:
                self._indexes["codes"].setdefault(language.codes.iso639_3, set()).add(lang_code)
            if language.codes.glottocode:
                self._indexes["codes"].setdefault(language.codes.glottocode, set()).add(lang_code)

            # Index names
            name_lower = language.name.lower()
            self._indexes["names"].setdefault(name_lower, set()).add(lang_code)

            # Index alternative names
            for alt_name in language.alternative_names:
                alt_lower = alt_name.lower()
                self._indexes["names"].setdefault(alt_lower, set()).add(lang_code)

    def get_all_languages(self) -> Iterator[Language]:
        """
        Get all languages as iterator.

        Returns:
            Iterator[Language]: An iterator over all languages.
        """
        if not self._loaded:
            self._load_data()
        return iter(self._languages.values())

    def search(self, query: str) -> List[Language]:
        """
        Search languages by name or code.

        Args:
            query: The search query string.

        Returns:
            List[Language]: List of matching languages.
        """
        if not self._loaded:
            self._load_data()

        query_lower = query.lower()
        results = []
        seen = set()

        # Search by code
        if query in self._languages:
            lang = self._languages[query]
            if lang.get_primary_code() not in seen:
                results.append(lang)
                seen.add(lang.get_primary_code())

        if "codes" in self._indexes and query in self._indexes["codes"]:
            for lang_code in self._indexes["codes"][query]:
                if lang_code not in seen:
                    results.append(self._languages[lang_code])
                    seen.add(lang_code)

        # Search by name
        if "names" in self._indexes and query_lower in self._indexes["names"]:
            for lang_code in self._indexes["names"][query_lower]:
                if lang_code not in seen:
                    results.append(self._languages[lang_code])
                    seen.add(lang_code)

        return results
