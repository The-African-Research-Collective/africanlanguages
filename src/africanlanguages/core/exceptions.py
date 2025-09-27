class AfricanLanguagesError(Exception):
    """Base exception for the package"""
    pass

class LanguageNotFoundError(AfricanLanguagesError):
    """Raised when a requested language is not found"""
    pass

class InvalidLanguageCodeError(AfricanLanguagesError):
    """Raised when language code format is invalid"""
    pass

class TextProcessingError(AfricanLanguagesError):
    """Raised when text processing fails"""
    pass

class DataLoadError(AfricanLanguagesError):
    """Raised when data loading fails"""
    pass

class ConfigurationError(AfricanLanguagesError):
    """Raised when configuration is invalid"""
    pass
