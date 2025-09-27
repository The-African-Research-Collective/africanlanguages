from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GeographicInfo:
    """Geographic information for a language"""

    countries: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    coordinates: Optional[Dict[str, float]] = None  # lat, lng


@dataclass
class LanguageCodes:
    """Various language code systems"""

    iso639_3: Optional[str] = None
    glottocode: Optional[str] = None


@dataclass
class Language:
    """Main language data model"""

    name: str
    codes: LanguageCodes
    geographic: GeographicInfo = field(default_factory=GeographicInfo)
    alternative_names: List[str] = field(default_factory=list)
    dialects: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize data after initialization"""
        self._validate()

    def _validate(self) -> None:
        """Validate language data consistency"""
        if not self.name:
            raise ValueError("Language name is required")
        if not (self.codes.iso639_3 or self.codes.glottocode):
            raise ValueError("At least one language code (ISO 639-3 or Glottocode) is required")

    def get_primary_code(self) -> Optional[str]:
        """Get the primary language code (prefer ISO 639-3)"""
        return self.codes.iso639_3 or self.codes.glottocode

    def in_country(self, country: str) -> bool:
        """Check if language is spoken in a country"""
        return country in self.geographic.countries
