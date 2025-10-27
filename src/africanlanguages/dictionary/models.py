from typing import List, Optional

from pydantic import BaseModel, Field

from africanlanguages.languages.models import Language
from africanlanguages.languages.registry import LanguageRegistry


class Translation(BaseModel):
    """Represents a translation of a word in another language."""

    text: str = Field(..., description="Translated text.")
    language: Optional[Language] = Field(None, description="Language of the translation.")
    context: Optional[str] = Field(None, description="Usage or contextual information.")


class DictionaryEntry(BaseModel):
    """Represents a single dictionary entry."""

    word: str = Field(..., description="The original word in a source language.")
    language: Optional[Language] = Field(..., description="Language object or code of the word.")
    part_of_speech: Optional[str] = Field(None, description="Part of speech")
    definition: Optional[str] = Field(None, description="Definition or meaning of the word in target language.")
    examples: Optional[List[str]] = Field(None, description="Example usage of the word.")
    translations: Optional[List[Translation]] = Field(None, description="Translations into other languages.")

    @classmethod
    def resolve_language(cls, lang_code_or_name: str) -> Optional[Language]:
        """Resolve language object from code or name using LanguageRegistry."""
        registry = LanguageRegistry()
        return registry.get_language(lang_code_or_name)
