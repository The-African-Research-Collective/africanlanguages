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
    """
    Mapping of dataset column names to internal fields.
    """

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
    **dataset_kwargs: Any,
) -> List[DictionaryEntry]:
    """
    Load dictionary dataset from Hugging Face.
    """

    config_name = config_name or source_lang
    logger.info(f"Loading dictionary for '{source_lang}'...")

    try:
        dataset = load_dataset(
            dataset_name,
            name=config_name,
            split=split,
            **dataset_kwargs,
        )
    except Exception as e:
        logger.error(f"Failed to load dictionary for '{source_lang}': {e}")
        raise

    entries: List[DictionaryEntry] = []

    for idx, row in enumerate(dataset):
        try:
            word = row.get(DictionaryFields.WORD.value)
            if not word:
                continue

            entry = DictionaryEntry(
                word=word,
                language=source_lang,
                part_of_speech=row.get(DictionaryFields.POS.value),
                definition=row.get(DictionaryFields.DEFINITION.value) or "",
                examples=row.get(DictionaryFields.EXAMPLES.value) or [],
                translations=row.get(DictionaryFields.TRANSLATIONS.value) or [],
            )
            entries.append(entry)
        except Exception as e:
            logger.warning(f"Skipping row {idx}: {e}")
            continue

    logger.info(f"Loaded {len(entries)} entries for '{source_lang}'.")
    return entries
