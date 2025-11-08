"""
Loader for language dictionaries dataset from Hugging Face.
"""

import logging
from enum import Enum
from typing import Any, List, Optional

from datasets import load_dataset

from africanlanguages.dictionary.models import DictionaryEntry

logger = logging.getLogger(__name__)

HGF_DICTIONARY_DATASET = "taresco/py_lang_dictionary"


class DictionaryFields(Enum):
    """Field names for dictionary dataset columns"""

    WORD = "word"
    POS = "pos"
    DEFINITION = "definition"
    EXAMPLES = "examples"
    TRANSLATIONS = "translations"


def load_dictionary(
    source_lang: str,
    dataset_name: str = HGF_DICTIONARY_DATASET,
    config_name: Optional[str] = None,
    split: str = "train",
    cache_dir: Optional[str] = None,
    **dataset_kwargs: Any,
) -> List[DictionaryEntry]:
    """Load any language dictionary dataset from Hugging Face.

    Args:
        source_lang: ISO code or name of the source language
        dataset_name: HF dataset id or path (default: "taresco/py_lang_dictionary").
        config_name: Optional configuration name for multi-config datasets.
        split: Dataset split to load (default: "train").
        cache_dir: Optional cache directory for datasets.
        **dataset_kwargs: Additional kwargs passed to `datasets.load_dataset`.

    Returns:
        A list of validated :class:`DictionaryEntry` instances.
    """

    data_file = f"{source_lang}_dictionary.csv"
    logger.info(f"Loading dataset '{dataset_name}' with data file '{data_file}' (split={split})...")

    try:
        dataset = load_dataset(
            dataset_name,
            data_files=data_file,
            name=config_name,
            split=split,
            cache_dir=cache_dir,
            **dataset_kwargs,
        )
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_name}': {e}")
        raise

    entries: List[DictionaryEntry] = []

    for idx, row in enumerate(dataset):
        try:
            entry = DictionaryEntry(
                word=row.get(DictionaryFields.WORD.value, "").strip(),
                language=source_lang,
                part_of_speech=row.get(DictionaryFields.POS.value) or None,
                definition=row.get(DictionaryFields.DEFINITION.value, "").strip(),
                examples=row.get(DictionaryFields.EXAMPLES.value),
                translations=row.get(DictionaryFields.TRANSLATIONS.value, []),
            )
            entries.append(entry)
        except Exception as e:
            logger.warning("Skipping row %d due to error: %s", idx, e)
            continue

    logger.info(f"Loaded {len(entries)} entries from dataset '{dataset_name}'.")
    return entries
