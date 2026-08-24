"""Load audited Afri-Dict configurations from Hugging Face."""

import json
import logging
from enum import Enum
from typing import Any, Optional

from datasets import DownloadConfig, load_dataset

from africanlanguages.core.exceptions import ConfigurationError, DataLoadError
from africanlanguages.dictionary.models import DictionaryAvailability, DictionaryEntry, Translation, UsageExample

logger = logging.getLogger(__name__)

HGF_DICTIONARY_DATASET = "taresco/afri-dict"
AFRI_DICT_REVISION = "99aad560786f8193d23c965a7a76d88d1faf639e"


class DictionaryFields(str, Enum):
    """Common viewer-friendly Afri-Dict columns."""

    WORD = "word"
    POS = "pos"
    DEFINITION = "definition"
    EXAMPLES = "examples"
    TRANSLATIONS = "translations"
    ENTRY_JSON = "entry_json"


_CONFIGS = {
    "hau": ("Hausa", "hau_v1", "en_hau_v1", "eng-to-hau"),
    "ibo": ("Igbo", "ibo_v1", "en_ibo_v1", "ibo-to-eng"),
    "swh": ("Swahili", "swh_v1", "en_swh_v1", "eng-to-swh"),
    "yor": ("Yoruba", "yor_v1", "en_yor_v1", "yor-to-eng"),
}
_ALIASES = {
    "ha": "hau",
    "hausa": "hau",
    "ig": "ibo",
    "igbo": "ibo",
    "sw": "swh",
    "swahili": "swh",
    "yo": "yor",
    "yoruba": "yor",
}


def normalize_language_code(language: str) -> str:
    """Resolve supported ISO 639-1, ISO 639-3, and English language names."""
    normalized = language.casefold().strip()
    normalized = _ALIASES.get(normalized, normalized)
    if normalized not in _CONFIGS:
        supported = ", ".join(sorted(_CONFIGS))
        raise ConfigurationError(f"Unsupported dictionary language {language!r}; choose one of: {supported}")
    return normalized


def available_dictionaries() -> list[DictionaryAvailability]:
    """Return the audited dictionary configurations supported by this package."""
    return [
        DictionaryAvailability(
            language_code=code,
            language_name=name,
            forward_config=forward,
            english_config=english,
            forward_direction=direction,
        )
        for code, (name, forward, english, direction) in _CONFIGS.items()
    ]


def resolve_dictionary_config(
    language: str,
    direction: str = "language",
    config_name: Optional[str] = None,
) -> tuple[str, str, str]:
    """Resolve a language and direction to ``(code, config, canonical direction)``."""
    code = normalize_language_code(language)
    _, forward_config, english_config, forward_direction = _CONFIGS[code]
    value = direction.casefold().strip().replace("_", "-")
    english_aliases = {
        "english",
        "reverse",
        "english-to-language",
        f"english-to-{code}",
        f"eng-to-{code}",
        f"english-to-{_CONFIGS[code][0].casefold()}",
    }
    language_aliases = {
        "forward",
        "canonical",
        "language",
        "language-to-english",
        f"{code}-to-eng",
        f"{_CONFIGS[code][0].casefold()}-to-english",
    }
    if value in english_aliases:
        canonical_direction = f"eng-to-{code}"
        automatic_config = english_config
    elif value in language_aliases:
        canonical_direction = f"{code}-to-eng"
        automatic_config = forward_config if forward_direction == canonical_direction else english_config
    else:
        raise ConfigurationError(f"Unsupported direction {direction!r} for {code!r}")

    if config_name:
        if config_name not in {forward_config, english_config}:
            raise ConfigurationError(f"Configuration {config_name!r} does not belong to {code!r}")
        return code, config_name, canonical_direction
    return code, automatic_config, canonical_direction


def _invert_entries(
    entries: list[DictionaryEntry],
    *,
    source_language: str,
    target_language: str,
) -> list[DictionaryEntry]:
    """Invert explicit translation candidates without indexing definition prose."""
    inverted: list[DictionaryEntry] = []
    for entry in entries:
        for candidate_number, candidate in enumerate(entry.translations, start=1):
            metadata = dict(entry.metadata)
            metadata["inverted_from"] = {
                "entry_id": entry.entry_id,
                "word": entry.word,
                "source_language": entry.language,
                "target_language": entry.target_language,
            }
            inverted.append(
                DictionaryEntry(
                    entry_id=f"{entry.entry_id or 'entry'}:inverse:{candidate_number}",
                    word=candidate.text,
                    language=source_language,
                    target_language=target_language,
                    part_of_speech=entry.part_of_speech,
                    definition=entry.word,
                    translations=[
                        Translation(
                            text=entry.word,
                            language=target_language,
                            context=candidate.context,
                            metadata={"inverted_from_candidate": candidate.metadata},
                        )
                    ],
                    audit_status=entry.audit_status,
                    source=entry.source,
                    metadata=metadata,
                )
            )
    return inverted


def _translation_from_candidate(candidate: dict[str, Any], target_language: str) -> Optional[Translation]:
    text = candidate.get("target_form") or candidate.get("text")
    if not text:
        return None
    return Translation(
        text=str(text),
        language=candidate.get("language") or target_language,
        source_form=candidate.get("target_source_form") or candidate.get("source_text"),
        review_flags=list(candidate.get("review_flags") or []),
        metadata=candidate,
    )


def _example_items(value: Any) -> list[Any]:
    """Return example objects from structured values or JSON-encoded columns."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        return decoded if isinstance(decoded, list) else [decoded]
    return value if isinstance(value, list) else [value]


def _usage_examples_from_row(
    row: dict[str, Any],
    canonical: dict[str, Any],
    *,
    source_language: str,
    target_language: str,
) -> list[UsageExample]:
    """Parse attested examples without deriving or inventing alignments."""
    pending: list[tuple[Any, Optional[str]]] = []
    pending.extend((item, None) for item in _example_items(canonical.get("usage_examples")))
    pending.extend((item, None) for item in _example_items(canonical.get("examples")))
    for sense_number, sense in enumerate(canonical.get("senses") or [], start=1):
        if not isinstance(sense, dict):
            continue
        sense_id = sense.get("sense_id") or sense.get("id") or f"sense:{sense_number}"
        pending.extend((item, str(sense_id)) for item in _example_items(sense.get("usage_examples")))
        pending.extend((item, str(sense_id)) for item in _example_items(sense.get("examples")))
    if not pending:
        pending.extend((item, None) for item in _example_items(row.get(DictionaryFields.EXAMPLES.value)))

    fallback_provenance = canonical.get("provenance") or {}
    examples: list[UsageExample] = []
    seen: set[tuple[Optional[str], str, str]] = set()
    for example_number, (item, inherited_sense_id) in enumerate(pending, start=1):
        if isinstance(item, str):
            text = item.strip()
            source = {}
            translation_value: Any = None
            raw = {"text": item}
        elif isinstance(item, dict):
            raw = item
            source = item.get("source") if isinstance(item.get("source"), dict) else {}
            text = str(source.get("text") or item.get("text") or item.get("source_text") or "").strip()
            translation_value = item.get("translation") or item.get("target") or item.get("target_text")
        else:
            continue
        if not text:
            continue

        translation: Optional[Translation] = None
        if isinstance(translation_value, dict):
            translation_text = str(translation_value.get("text") or "").strip()
            if translation_text:
                translation = Translation(
                    text=translation_text,
                    language=str(translation_value.get("language") or target_language),
                    source_form=translation_value.get("source_form"),
                    review_flags=list(translation_value.get("review_flags") or []),
                    metadata=dict(translation_value.get("metadata") or {}),
                )
        elif translation_value is not None and str(translation_value).strip():
            translation = Translation(text=str(translation_value).strip(), language=target_language)

        sense_id = raw.get("sense_id") or inherited_sense_id
        key = (str(sense_id) if sense_id else None, text, translation.text if translation else "")
        if key in seen:
            continue
        seen.add(key)
        examples.append(
            UsageExample(
                example_id=raw.get("example_id") or f"{row.get('entry_id') or 'entry'}:example:{example_number}",
                sense_id=str(sense_id) if sense_id else None,
                text=text,
                language=str(source.get("language") or raw.get("language") or source_language),
                translation=translation,
                evidence_status=raw.get("evidence_status") or "source_attested_unreviewed",
                review_flags=list(raw.get("review_flags") or []),
                provenance=dict(raw.get("provenance") or fallback_provenance),
                metadata=raw,
            )
        )
    return examples


def _entry_from_row(row: dict[str, Any], default_language: str) -> DictionaryEntry:
    raw_object = row.get(DictionaryFields.ENTRY_JSON.value)
    canonical = json.loads(raw_object) if raw_object else {}
    language = row.get("language") or default_language
    target_language = row.get("target_language") or canonical.get("language") or "eng"

    candidates: list[dict[str, Any]] = []
    if "english" in canonical:
        candidates.extend(canonical.get("translations") or [])
    else:
        for sense in canonical.get("senses") or []:
            candidates.extend(sense.get("translations") or [])
    translations = [
        translation
        for candidate in candidates
        if (translation := _translation_from_candidate(candidate, target_language)) is not None
    ]
    usage_examples = _usage_examples_from_row(
        row,
        canonical,
        source_language=str(language),
        target_language=str(target_language),
    )

    metadata = canonical or {
        "forms": json.loads(row.get("forms_json") or "[]"),
        "senses": json.loads(row.get("senses_json") or "[]"),
        "cross_references": json.loads(row.get("cross_references_json") or "[]"),
        "provenance": json.loads(row.get("provenance_json") or "{}"),
        "audit": json.loads(row.get("audit_json") or "{}"),
    }
    return DictionaryEntry(
        entry_id=row.get("entry_id") or canonical.get("entry_id"),
        word=str(row.get(DictionaryFields.WORD.value) or "").strip(),
        language=str(language),
        target_language=str(target_language) if target_language else None,
        part_of_speech=row.get(DictionaryFields.POS.value) or None,
        definition=row.get(DictionaryFields.DEFINITION.value) or None,
        examples=[example.text for example in usage_examples],
        usage_examples=usage_examples,
        translations=translations,
        audit_status=row.get("audit_status") or None,
        source="afridict",
        metadata=metadata,
    )


def load_dictionary(
    source_lang: str,
    dataset_name: str = HGF_DICTIONARY_DATASET,
    config_name: Optional[str] = None,
    direction: str = "language",
    split: str = "train",
    cache_dir: Optional[str] = None,
    revision: Optional[str] = AFRI_DICT_REVISION,
    offline: bool = False,
    strict: bool = True,
    **dataset_kwargs: Any,
) -> list[DictionaryEntry]:
    """Load one audited dictionary configuration.

    Data is cached by :mod:`datasets`. Set ``offline=True`` to require an
    already-cached copy and avoid network access.
    """
    code, resolved_config, resolved_direction = resolve_dictionary_config(source_lang, direction, config_name)
    download_config = dataset_kwargs.pop("download_config", None) or DownloadConfig(
        cache_dir=cache_dir,
        local_files_only=offline,
    )
    try:
        dataset = load_dataset(
            dataset_name,
            name=resolved_config,
            split=split,
            cache_dir=cache_dir,
            revision=revision,
            download_config=download_config,
            **dataset_kwargs,
        )
    except Exception as exc:
        mode = "cached" if offline else "remote or cached"
        raise DataLoadError(
            f"Could not load {resolved_config!r} from {dataset_name!r} using {mode} data: {exc}"
        ) from exc

    entries: list[DictionaryEntry] = []
    errors: list[str] = []
    for index, dataset_row in enumerate(dataset):
        try:
            entries.append(_entry_from_row(dict(dataset_row), code))
        except Exception as exc:
            errors.append(f"row {index}: {exc}")

    if errors and strict:
        raise DataLoadError(f"Rejected {len(errors)} rows from {resolved_config!r}; first error: {errors[0]}")
    if errors:
        logger.warning("Skipped %d invalid rows from %s", len(errors), resolved_config)
    requested_source, requested_target = resolved_direction.split("-to-")
    if entries and entries[0].language != requested_source:
        inverted = _invert_entries(
            entries,
            source_language=requested_source,
            target_language=requested_target,
        )
        if not inverted:
            raise DataLoadError(
                f"Could not safely build {resolved_direction!r} from {resolved_config!r}: "
                "the source contains no explicit translation candidates"
            )
        entries = inverted
    return entries
