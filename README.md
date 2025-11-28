# africanlanguages

[![PyPI](https://img.shields.io/pypi/v/africanlanguages)](https://pypi.org/project/africanlanguages/)
[![Python](https://img.shields.io/pypi/pyversions/africanlanguages)](https://pypi.org/project/africanlanguages/)
[![License](https://img.shields.io/pypi/l/africanlanguages)](https://github.com/The-African-Research-Collective/africanlanguages/blob/main/LICENSE)


**africanlanguages** provides foundational tools for working with African languages in Python. Currently, it offers validated language metadata for **2,375 languages** and a high-performance dictionary interface for word-level and sentence-level lookups across **4 African languages** (~29,000 entries).

## Installation

```bash
pip install africanlanguages
```

## What's Inside

| Module | Coverage | Performance |
|--------|----------|-------------|
| **Languages** | 2,375 languages with ISO 639-3, Glottolog codes, families, geographic data | O(1) lookup |
| **Dictionary** | ~29,000 entries across Yoruba, Swahili, Hausa, Igbo | O(1) exact, O(n) fuzzy |

## Quick Start

### Language Discovery

```python
from africanlanguages import get_language_by_code, search_languages, get_languages_by_country

# Get language by ISO 639-3 or Glottolog code
yoruba = get_language_by_code("yor")
print(f"{yoruba.name} ({yoruba.family})")  # Yoruba (Atlantic-Congo)

# Search by name
results = search_languages("Swahili")

# Get all languages in a country
nigerian_langs = get_languages_by_country("Nigeria")
```

### Dictionary Lookup

```python
from africanlanguages.dictionary import Dictionary

yor_dict = Dictionary("yor")

# Exact lookup
results = yor_dict.lookup("aja")
print(results[0].definition)  # "dog"

# Fuzzy search (handles typos)
results = yor_dict.lookup("omi", exact_match=False) #water

# Reverse lookup (English → Yoruba)
results = yor_dict.lookup("water", exact_match=False)

# Sentence lookup
results = yor_dict.lookup_sentence("Mo lọ sí ilé-ìwé") # I went to school
```

## Use Cases
- Standardize language codes across African NLP datasets
- Build language learning applications with instant word lookup
- Analyze linguistic diversity and language family distributions
- Create translation tools for low-resource African languages

## API Reference

### Language Module

```python
get_language_by_code(code: str) -> Optional[Language]
search_languages(query: str) -> List[Language]
get_languages_by_country(country: str) -> List[Language]
get_languages_by_region(region: str) -> List[Language]
get_all_language_families() -> List[str]
get_language_count() -> int
```

### Dictionary Module

```python
dictionary = Dictionary(language_code: str)

dictionary.lookup(
    word: str,
    exact_match: bool = True,
    top_n: int = 2,
    threshold: float = 0.6
) -> List[DictionaryEntry]

dictionary.lookup_sentence(
    sentence: str,
    exact_match: bool = True,
    simple: bool = True
) -> Dict[str, Any]
```

📓 [Dictionary notebook](https://github.com/The-African-Research-Collective/africanlanguages/blob/main/notebooks/dictionary_utility.ipynb)


<!--
## Contributing

We're working on more dictionary languages, IPA transcriptions, audio pronunciations, and cross-language lookups.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
## Setup

You'll need to [install uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods).

* Install `africanlanguages` by running `uv sync`

* Run `pre-commit install`

## Notes on Dependencies

- [Extra dependency](https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies): published along with the package.
- [Dependency group](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups): only used during development.

## Citation

```bibtex
@software{africanlanguages2025,
  title = {africanlanguages: A Python Package for African Language Resources},
  author = {The African Research Collective},
  year = {2025},
  url = {https://github.com/The-African-Research-Collective/africanlanguages}
}
```

## Links
-->


