"""Data models for dictionary entries."""

from typing import List, Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from africanlanguages.languages.models import Language
from africanlanguages.languages.registry import LanguageRegistry

_language_registry = LanguageRegistry()


class Translation(BaseModel):
    """Represents a translation of a word in another language."""

    text: str = Field(..., description="Translated text.")
    language: str = Field(..., description="Language of the translation.")
    context: Optional[str] = Field(None, description="Usage or contextual information.")


class DictionaryEntry(BaseModel):
    """Represents a single dictionary entry."""

    word: str = Field(..., description="The original word in a source language.")
    language: str = Field(..., description="Language code of the word.")
    part_of_speech: Optional[str] = Field(None, description="Part of speech")
    definition: Optional[str] = Field(None, description="Definition or meaning of the word in target language.")
    examples: Optional[List[str]] = Field(None, description="Example usage of the word.")
    translations: Optional[List[Translation]] = Field(None, description="Translations into other languages.")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate that language code is provided and non-empty."""
        if not v or not v.strip():
            raise ValueError("Language code is required and cannot be empty")
        return v.strip()

    @classmethod
    def resolve_language(cls, lang_code: str) -> Optional[Language]:
        return _language_registry.get_language(lang_code)
