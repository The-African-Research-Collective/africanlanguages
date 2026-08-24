"""Public data models for dictionary results and metadata."""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from africanlanguages.languages.models import Language
from africanlanguages.languages.registry import LanguageRegistry

_language_registry = LanguageRegistry()


class Translation(BaseModel):
    """A source-backed translation candidate."""

    text: str = Field(..., description="Translated text.")
    language: str = Field(..., description="ISO 639-3 target-language code.")
    context: Optional[str] = Field(None, description="Usage or contextual information.")
    source_form: Optional[str] = Field(None, description="Source-attested form when it differs from text.")
    review_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text", "language")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty")
        return value


class DictionaryEntry(BaseModel):
    """A dictionary headword with its source-backed meanings and evidence."""

    word: str = Field(..., description="Lookup headword.")
    language: str = Field(..., description="ISO 639-3 language code of the headword.")
    target_language: Optional[str] = Field(None, description="Primary target-language code.")
    entry_id: Optional[str] = Field(None, description="Stable dataset entry identifier.")
    part_of_speech: Optional[str] = Field(None, description="Part of speech.")
    definition: Optional[str] = Field(None, description="Source-backed definition or compact gloss.")
    examples: list[str] = Field(default_factory=list)
    translations: list[Translation] = Field(default_factory=list)
    audit_status: Optional[str] = Field(None, description="Source audit disposition.")
    source: Optional[str] = Field(None, description="Provider that supplied this result.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Lossless canonical dataset object.")

    @field_validator("word", "language")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty")
        return value

    @property
    def provenance(self) -> Any:
        """Return provenance exactly as represented by the audited object."""
        return self.metadata.get("provenance")

    @property
    def review(self) -> Any:
        """Return the canonical review or audit object, when available."""
        return self.metadata.get("review") or self.metadata.get("audit")

    @classmethod
    def resolve_language(cls, lang_code: str) -> Optional[Language]:
        return _language_registry.get_language(lang_code)


class DictionaryMetadata(BaseModel):
    """Description of a loaded dictionary configuration."""

    language_code: str
    config_name: str
    dataset_name: str
    revision: Optional[str]
    direction: str
    source_language: str
    target_language: str
    entry_count: int
    providers: list[str] = Field(default_factory=list)


class DictionaryAvailability(BaseModel):
    """A versioned dictionary configuration available from Afri-Dict."""

    language_code: str
    language_name: str
    forward_config: str
    english_config: str
    forward_direction: str
