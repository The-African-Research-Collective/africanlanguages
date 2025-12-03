"""Data models for dictionary entries."""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class Translation(BaseModel):
    """Represents a detailed translation object."""

    text: str = Field(..., description="Translated text.")
    language: Optional[str] = Field(None, description="Language of the translation")
    context: Optional[str] = Field(None, description="Usage context.")


class DictionaryEntry(BaseModel):
    """Represents a single dictionary entry."""

    word: str = Field(..., description="The original word in a source language.")
    language: str = Field(..., description="Language code of the word.")
    part_of_speech: Optional[str] = Field(None, description="Part of speech")
    definition: Optional[str] = Field(None, description="Definition or meaning of the word in target language.")
    examples: List[str] = Field(default_factory=list, description="Example usage of the word.")
    translations: List[Union[Translation, str]] = Field(
        default_factory=list, description="Translations into other languages."
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Language code is required")
        return v.strip()
