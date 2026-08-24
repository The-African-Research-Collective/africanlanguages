"""High-level dictionary interface."""

from collections.abc import Sequence
from typing import Any, Optional

from africanlanguages.dictionary.loader import (
    AFRI_DICT_REVISION,
    HGF_DICTIONARY_DATASET,
    available_dictionaries,
    resolve_dictionary_config,
)
from africanlanguages.dictionary.models import DictionaryAvailability, DictionaryEntry, DictionaryMetadata, UsageExample
from africanlanguages.dictionary.providers import AfriDictProvider, DictionaryProvider
from africanlanguages.dictionary.query import DictionaryQuery


class Dictionary:
    """Query one language through Afri-Dict or a list of bilingual providers."""

    def __init__(
        self,
        language_code: str,
        direction: str = "language",
        *,
        entries: Optional[list[DictionaryEntry]] = None,
        providers: Optional[Sequence[DictionaryProvider | str]] = None,
        dataset_name: str = HGF_DICTIONARY_DATASET,
        config_name: Optional[str] = None,
        revision: Optional[str] = AFRI_DICT_REVISION,
        **loader_kwargs: Any,
    ):
        code, resolved_config, resolved_direction = resolve_dictionary_config(language_code, direction, config_name)
        self.language_code = code
        self.direction = resolved_direction
        self.config_name = resolved_config
        self.dataset_name = dataset_name
        self.revision = revision
        if entries is not None and providers is not None:
            raise ValueError("Pass either entries or providers, not both")

        self.providers: list[DictionaryProvider] = []
        if entries is not None:
            self.entries = entries
        else:
            requested = list(providers) if providers is not None else ["afridict"]
            for provider in requested:
                if provider == "afridict":
                    self.providers.append(
                        AfriDictProvider(
                            dataset_name=dataset_name,
                            config_name=resolved_config,
                            revision=revision,
                            **loader_kwargs,
                        )
                    )
                elif isinstance(provider, DictionaryProvider):
                    self.providers.append(provider)
                else:
                    raise ValueError(f"Unknown dictionary provider {provider!r}")
            self.entries = [
                entry for provider in self.providers for entry in provider.load(self.language_code, self.direction)
            ]
        self._query = DictionaryQuery(self.entries)

    @staticmethod
    def languages() -> list[DictionaryAvailability]:
        """List dictionary-backed languages and their configurations."""
        return available_dictionaries()

    def lookup(self, word: str, *, normalization_aware: bool = True) -> list[DictionaryEntry]:
        """Look up a headword exactly, with optional hyphen/spacing equivalence."""
        return self._query.search(word, normalization_aware=normalization_aware)

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
        """Search exact, prefix, or fuzzy headword matches."""
        return self._query.search(
            word,
            fuzzy=fuzzy,
            threshold=threshold,
            normalization_aware=normalization_aware,
            prefix=prefix,
            limit=limit,
        )

    def prefix(self, value: str, limit: int = 20) -> list[DictionaryEntry]:
        """Return normalization-aware prefix matches."""
        return self._query.prefix(value, limit=limit)

    def lookup_many(self, words: list[str]) -> dict[str, list[DictionaryEntry]]:
        """Look up multiple words in one in-memory pass."""
        return self._query.lookup_many(words)

    def examples(
        self,
        word: str,
        *,
        sense_id: str | None = None,
        limit: int | None = None,
    ) -> list[UsageExample]:
        """Return source-backed usage examples for a headword or one sense."""
        if limit is not None and limit <= 0:
            return []
        results = [
            example
            for entry in self.lookup(word)
            for example in entry.usage_examples
            if sense_id is None or example.sense_id == sense_id
        ]
        return results[:limit] if limit is not None else results

    def define(self, word: str, fuzzy: bool = False) -> list[str]:
        """Return source-backed definitions for a word."""
        return self._query.get_definitions(word, fuzzy=fuzzy)

    def metadata(self) -> DictionaryMetadata:
        """Describe the loaded configuration and pinned dataset revision."""
        source = self.entries[0].language if self.entries else self.direction.split("-to-")[0]
        target = self.entries[0].target_language if self.entries else self.direction.split("-to-")[-1]
        return DictionaryMetadata(
            language_code=self.language_code,
            config_name=self.config_name,
            dataset_name=self.dataset_name,
            revision=self.revision,
            direction=self.direction,
            source_language=source,
            target_language=target or "eng",
            entry_count=len(self.entries),
            providers=self.provider_names,
        )

    @property
    def provider_names(self) -> list[str]:
        """Return provider names in lookup-precedence order."""
        if self.providers:
            return [provider.name for provider in self.providers]
        return sorted({entry.source for entry in self.entries if entry.source})

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"Dictionary(language={self.language_code!r}, config={self.config_name!r}, entries={len(self)})"
