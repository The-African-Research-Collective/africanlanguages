"""
Loader for language dictionaries dataset from Hugging Face.
"""

import logging
from typing import List, Optional

from datasets import load_dataset

from .models import DictionaryEntry

logger = logging.getLogger(__name__)


def load_dictionary(
    dataset_name: str, source_lang: str, split: str = "train", cache_dir: Optional[str] = None
) -> List[DictionaryEntry]:
    """
    Load any language dictionary dataset from Hugging Face.

    Args:
        dataset_name: Name of the Hugging Face dataset
        source_lang: ISO code or name of the source language (e.g., "yor" or "Yoruba")
        split: Dataset split to load (default "train")
        cache_dir: Optional directory to cache downloaded dataset

    Returns:
        List of DictionaryEntry objects
    """
    logger.info(f"Loading dataset '{dataset_name}' (split={split})...")

    try:
        dataset = load_dataset(dataset_name, split=split, cache_dir=cache_dir)
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_name}': {e}")
        raise

    entries: List[DictionaryEntry] = []
    for idx, row in enumerate(dataset):
        try:
            entry = DictionaryEntry(
                word=row.get("word", "").strip(),
                language=DictionaryEntry.resolve_language(source_lang),
                part_of_speech=row.get("pos"),
                definition=row.get("definition", "").strip(),
                examples=row.get("examples", []),
                translations=row.get("translations", []),
            )
            entries.append(entry)
        except Exception as e:
            logger.warning(f"Skipping row {idx} due to error: {e}")
            continue

    logger.info(f"Loaded {len(entries)} entries from dataset '{dataset_name}'.")
    return entries


# Convenience wrapper for Yoruba (optional)
def load_yoruba_dict(split: str = "train", cache_dir: Optional[str] = None) -> List[DictionaryEntry]:
    return load_dictionary(
        dataset_name="adeleyi/py_yor_dict",
        source_lang="yor",
        split=split,
        cache_dir=cache_dir,
    )
