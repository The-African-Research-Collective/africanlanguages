# **africanlanguages**

[![PyPI](https://img.shields.io/pypi/v/africanlanguages)](https://pypi.org/project/africanlanguages/)
[![Python](https://img.shields.io/pypi/pyversions/africanlanguages)](https://pypi.org/project/africanlanguages/)
[![License](https://img.shields.io/pypi/l/africanlanguages)](https://github.com/The-African-Research-Collective/africanlanguages/blob/main/LICENSE)

`africanlanguages` is a Python package designed for African language processing. It provides two main things: language metadata for 2,375 African languages (ISO codes, language families, geographic data) and dictionary lookup for 4 languages with about 29,000 entries.

## **Motivation**
There's a major gap in tools for working with African languages in Python. While other languages like Arabic have useful packages like PyArabic, nothing similar exists for African languages. Existing NLP tools either exclude African languages entirely or provide only minimal support. This means developers and researchers have to build everything from scratch or use general tools that don't work well for African languages. This makes it much harder to create applications or do research with African languages, which slows down progress in this important area.



## **Package Overview**
 `africanlanguages`currently provides two main functionalities:
###  **Language Discovery**
A registry that provides verified information about African languages. It allows users to find language codes (ISO 639-3, Glottolog), language families, and geographic distribution (countries and regions). It provides a standardized language metadata for NLP workflows. Useful for mapping language codes across datasets as well as building geographic visualizations of language distribution.

### **Dictionary**
A dictionary interface for looking up words and their meanings. It supports bidirectional word lookup between African languages and English, and sentence lookup to process multiple words at once. It can be used in translation pipelines for word-level text conversion. Can also be embedded into language learning apps to provide instant word definitions and example sentences.

## Installation

```bash
pip install africanlanguages
```

## **Modules**
### **Languages Module**

 **Coverage:** Information on **2,375 African languages** stored in JSON format.


| Data Field | Description |
|------------|-------------|
| `name` | Standard language name |
| `iso639_3` | ISO 639-3 code |
| `glottocode` | Glottolog identifier |
| `family` | Language family |
| `country` | Primary country |
| `macro_area` | Geographic region |
| `latitude/longitude` | Coordinates |


**Architecture:**
The module is organized into three components:
1. Data Model (`models.py`) — Uses Python dataclasses to create structured blueprints for language entries.  
2. Registry (`registry.py`) — This implements fast indexing for lookups by name, ISO code, or Glottocode. Uses a Singleton pattern to load data once and share across all queries.
3. Discovery Interface (`discovery.py`) — Provides a user-friendly API for complex queries. It supports method chaining so developers can stack filters.

 **Features:**
 - Retrieve complete language objects by ISO 639-3 or Glottocode.
 - List all unique language families in the database
 - Build sophisticated queries using method chaining
 - Access geographic data (coordinates, countries, regions)


```python
from africanlanguages import get_languages_by_country

nigerian_langs = get_languages_by_country("Nigeria")
print(f"Total Languages in Nigeria: {len(nigerian_langs)}")

#output: Total Languages in Nigeria: 552
```

### **Dictionary Module**
- Data Source: Language dictionaries hosted on [Hugging Face](https://huggingface.co/datasets/taresco/py_lang_dictionary)

**Current Coverage:** Yoruba, Swahili, Hausa, Igbo

**Architecture:**
This module has three main components:
1. Data Model (`models.py`) — Uses Pydantic to enforce strict type checking at runtime. Every word, definition, and part of speech must conform to a defined schema, preventing malformed entries from breaking the system.The data model is designed to support more fields than currently available in the dataset. This includes `examples` (for usage sentences) and `translations` (for cross-African language lookups,e.g. Yoruba → Swahili). The current dataset provides `word`, `part of speech`, and `definitions`.

2. Loader (`loader.py`) — It handles connection to and extraction from the Hugging Face dataset repository.

3. Query (`query.py`) —  This handles the search logic. It builds an index over both headwords and definitions, enabling bidirectional lookup (African language ↔ English). Supports exact matching (direct index lookup) and fuzzy matching (similarity scoring using SequenceMatcher). The `find_matches()` method tries exact match first, falls back to fuzzy search if enabled, and returns top N results sorted by similarity score above a given threshold.

**Features**
- Exact lookup — Find a word when you know the exact spelling
- Fuzzy lookup — Find words even with typos or uncertain spelling
- Reverse lookup
- Sentence lookup — Process multiple words at once
- Configurable search parameters — Adjust similarity threshold and number of results returned.

**For usage examples,see**: [ Dictionary Utility Notebook](https://github.com/The-African-Research-Collective/africanlanguages/blob/feat/dictionary-module/notebooks/dict_utility_notebook.ipynb)


## Citation

```bibtex
@software{africanlanguages2025,
  title = {africanlanguages: A Python Package for African Language Resources},
  author = {The African Research Collective},
  year = {2025},
  url = {https://github.com/The-African-Research-Collective/africanlanguages}
}
```


