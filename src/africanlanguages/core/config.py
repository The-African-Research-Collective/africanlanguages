from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import Singleton


@dataclass
class DataPaths:
    """Configuration for data file paths"""

    languages_db: Path = Path("data/languages.json")


@dataclass
class PackageConfig:
    """Main package configuration"""

    data_paths: DataPaths = field(default_factory=DataPaths)


class ConfigManager(metaclass=Singleton):
    """Global configuration manager"""

    def __init__(self):
        self.config = PackageConfig()
        self._load_user_config()

    def _load_user_config(self) -> None:
        """Load user configuration from file or environment"""
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split(".")
        value = self.config
        try:
            for k in keys:
                value = getattr(value, k)
            return value
        except AttributeError:
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split(".")
        obj = self.config
        for k in keys[:-1]:
            if not hasattr(obj, k):
                setattr(obj, k, type(obj)())
            obj = getattr(obj, k)
        setattr(obj, keys[-1], value)
