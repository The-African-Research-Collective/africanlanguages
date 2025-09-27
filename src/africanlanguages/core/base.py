from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class ProcessingResult:
    """Base result class for processing operations"""
    success: bool
    data: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseProcessor(ABC):
    """Abstract base class for all processors"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._setup()

    @abstractmethod
    def _setup(self) -> None:
        """Initialize processor-specific setup"""
        pass

    @abstractmethod
    def process(self, data: Any, **kwargs) -> ProcessingResult:
        """Process input data and return result"""
        pass

class Singleton(type):
    """Metaclass for singleton pattern"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
