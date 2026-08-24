"""Pluggable sources for bilingual dictionary entries."""

import csv
import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from africanlanguages.core.exceptions import ConfigurationError, DataLoadError
from africanlanguages.dictionary.loader import AFRI_DICT_REVISION, HGF_DICTIONARY_DATASET, load_dictionary
from africanlanguages.dictionary.models import DictionaryEntry, Translation

_WIKTIONARY_LANGUAGE_CODES = {
    "hau": {"ha", "hau"},
    "ibo": {"ig", "ibo"},
    "swh": {"sw", "swa", "swh"},
    "yor": {"yo", "yor"},
}


class DictionaryProvider(ABC):
    """A source capable of producing normalized bilingual entries."""

    name: str

    @abstractmethod
    def load(self, language_code: str, direction: str) -> list[DictionaryEntry]:
        """Load entries for a canonical direction such as ``ibo-to-eng``."""


class AfriDictProvider(DictionaryProvider):
    """Load one of the audited Afri-Dict configurations."""

    name = "afridict"

    def __init__(
        self,
        *,
        dataset_name: str = HGF_DICTIONARY_DATASET,
        config_name: Optional[str] = None,
        revision: Optional[str] = AFRI_DICT_REVISION,
        **loader_kwargs: Any,
    ):
        self.dataset_name = dataset_name
        self.config_name = config_name
        self.revision = revision
        self.loader_kwargs = loader_kwargs

    def load(self, language_code: str, direction: str) -> list[DictionaryEntry]:
        entries = load_dictionary(
            source_lang=language_code,
            direction=direction,
            dataset_name=self.dataset_name,
            config_name=self.config_name,
            revision=self.revision,
            **self.loader_kwargs,
        )
        for entry in entries:
            entry.source = self.name
            entry.metadata.setdefault("provider", self.name)
        return entries


class DelimitedFileProvider(DictionaryProvider):
    """Read a two-column bilingual CSV or TSV file in either direction.

    Each row represents one attested mapping. The raw row and its line number
    remain attached to the result so callers can audit where a mapping came
    from. No attempt is made to split definitions or infer extra translations.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        language: str,
        source_column: str,
        english_column: str,
        name: Optional[str] = None,
        delimiter: Optional[str] = None,
        part_of_speech_column: Optional[str] = None,
        context_column: Optional[str] = None,
        encoding: str = "utf-8-sig",
        strict: bool = True,
        attribution: Optional[str] = None,
        license: Optional[str] = None,
    ):
        self.path = Path(path)
        self.language = language.casefold().strip()
        self.source_column = source_column
        self.english_column = english_column
        self.name = name or self.path.stem
        self.delimiter = delimiter or ("\t" if self.path.suffix.casefold() in {".tsv", ".tab"} else ",")
        self.part_of_speech_column = part_of_speech_column
        self.context_column = context_column
        self.encoding = encoding
        self.strict = strict
        self.attribution = attribution
        self.license = license

    def load(self, language_code: str, direction: str) -> list[DictionaryEntry]:
        if language_code != self.language:
            raise ConfigurationError(
                f"Provider {self.name!r} contains {self.language!r}, not requested language {language_code!r}"
            )
        if not self.path.is_file():
            raise DataLoadError(f"Bilingual mapping file does not exist: {self.path}")

        reverse = direction.startswith("eng-to-")
        entries: list[DictionaryEntry] = []
        errors: list[str] = []
        with self.path.open("r", encoding=self.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self.delimiter)
            required = {self.source_column, self.english_column}
            missing = required.difference(reader.fieldnames or [])
            if missing:
                raise DataLoadError(f"Provider {self.name!r} is missing columns: {', '.join(sorted(missing))}")

            for line_number, raw_row in enumerate(reader, start=2):
                row = {str(key): value for key, value in raw_row.items() if key is not None}
                source_text = str(row.get(self.source_column) or "").strip()
                english_text = str(row.get(self.english_column) or "").strip()
                if not source_text or not english_text:
                    errors.append(f"line {line_number}: empty source or English value")
                    continue
                entries.append(self._entry(row, line_number, source_text, english_text, reverse))

        if errors and self.strict:
            raise DataLoadError(f"Rejected {len(errors)} rows from {self.name!r}; first error: {errors[0]}")
        return entries

    def _entry(
        self,
        row: dict[str, Any],
        line_number: int,
        source_text: str,
        english_text: str,
        reverse: bool,
    ) -> DictionaryEntry:
        word = english_text if reverse else source_text
        translated = source_text if reverse else english_text
        entry_language = "eng" if reverse else self.language
        target_language = self.language if reverse else "eng"
        context = str(row.get(self.context_column) or "").strip() if self.context_column else None
        part_of_speech = (
            str(row.get(self.part_of_speech_column) or "").strip() or None if self.part_of_speech_column else None
        )
        provenance = {
            "provider": self.name,
            "file": self.path.name,
            "line": line_number,
            "attribution": self.attribution,
            "license": self.license,
        }
        fingerprint = json.dumps(
            {"provider": self.name, "language": self.language, "row": row},
            ensure_ascii=False,
            sort_keys=True,
        ).encode()
        provider_key = re.sub(r"[^a-z0-9]+", "-", self.name.casefold()).strip("-") or "external"
        entry_id = f"{provider_key}:{hashlib.sha256(fingerprint).hexdigest()[:20]}"
        return DictionaryEntry(
            entry_id=entry_id,
            word=word,
            language=entry_language,
            target_language=target_language,
            part_of_speech=part_of_speech,
            definition=translated,
            translations=[
                Translation(
                    text=translated,
                    language=target_language,
                    context=context,
                    metadata={"provider": self.name, "provenance": provenance},
                )
            ],
            source=self.name,
            audit_status="external_source_unreviewed",
            metadata={"provider": self.name, "provenance": provenance, "raw": row},
        )


class FreeDictProvider(DictionaryProvider):
    """Read a downloaded FreeDict TEI dictionary without redistributing it."""

    def __init__(
        self,
        path: str | Path,
        *,
        language: str,
        source_is_english: bool = False,
        name: Optional[str] = None,
        attribution: str = "FreeDict",
        license: Optional[str] = None,
    ):
        self.path = Path(path)
        self.language = language.casefold().strip()
        self.source_is_english = source_is_english
        self.name = name or f"freedict-{self.path.stem}"
        self.attribution = attribution
        self.license = license

    def load(self, language_code: str, direction: str) -> list[DictionaryEntry]:
        if language_code != self.language:
            raise ConfigurationError(
                f"Provider {self.name!r} contains {self.language!r}, not requested language {language_code!r}"
            )
        if not self.path.is_file():
            raise DataLoadError(f"FreeDict TEI file does not exist: {self.path}")
        try:
            root = ET.parse(self.path).getroot()
        except ET.ParseError as exc:
            raise DataLoadError(f"Could not parse FreeDict TEI file {self.path}: {exc}") from exc

        reverse = direction.startswith("eng-to-")
        entries: list[DictionaryEntry] = []
        for entry_number, element in enumerate(root.findall(".//{*}entry"), start=1):
            source_forms = [self._text(node) for node in element.findall("./{*}form/{*}orth")]
            translations = [self._text(node) for node in element.findall(".//{*}cit[@type='trans']/{*}quote")]
            source_forms = [value for value in source_forms if value]
            translations = [value for value in translations if value]
            if not source_forms or not translations:
                continue
            pos_node = element.find(".//{*}gramGrp/{*}pos")
            part_of_speech = self._text(pos_node) if pos_node is not None else None
            xml_id = element.get("{http://www.w3.org/XML/1998/namespace}id")
            for form_number, source_form in enumerate(source_forms, start=1):
                for translation_number, translated_form in enumerate(translations, start=1):
                    english_text = source_form if self.source_is_english else translated_form
                    language_text = translated_form if self.source_is_english else source_form
                    entries.append(
                        self._entry(
                            english_text=english_text,
                            language_text=language_text,
                            reverse=reverse,
                            part_of_speech=part_of_speech,
                            xml_id=xml_id,
                            entry_number=entry_number,
                            form_number=form_number,
                            translation_number=translation_number,
                        )
                    )
        return entries

    @staticmethod
    def _text(element: ET.Element) -> str:
        return " ".join("".join(element.itertext()).split())

    def _entry(
        self,
        *,
        english_text: str,
        language_text: str,
        reverse: bool,
        part_of_speech: Optional[str],
        xml_id: Optional[str],
        entry_number: int,
        form_number: int,
        translation_number: int,
    ) -> DictionaryEntry:
        word = english_text if reverse else language_text
        translated = language_text if reverse else english_text
        entry_language = "eng" if reverse else self.language
        target_language = self.language if reverse else "eng"
        provenance = {
            "provider": self.name,
            "file": self.path.name,
            "tei_entry_id": xml_id,
            "tei_entry_number": entry_number,
            "attribution": self.attribution,
            "license": self.license,
        }
        fingerprint = f"{self.name}\0{xml_id or entry_number}\0{form_number}\0{translation_number}"
        entry_id = f"{self.name}:{hashlib.sha256(fingerprint.encode()).hexdigest()[:20]}"
        return DictionaryEntry(
            entry_id=entry_id,
            word=word,
            language=entry_language,
            target_language=target_language,
            part_of_speech=part_of_speech,
            definition=translated,
            translations=[Translation(text=translated, language=target_language)],
            source=self.name,
            audit_status="external_source_unreviewed",
            metadata={"provider": self.name, "provenance": provenance},
        )


class WiktextractProvider(DictionaryProvider):
    """Read filtered Wiktextract JSONL or JSONL.GZ files.

    Native-language lookups use English glosses on entries whose ``lang_code``
    is the requested language. English lookups use only explicit translation
    objects on English entries; gloss prose is never reverse-indexed.
    """

    name = "wiktionary"

    def __init__(
        self,
        language_path: str | Path,
        *,
        language: str,
        english_path: str | Path | None = None,
        edition: str = "enwiktionary",
        dump_revision: Optional[str] = None,
        attribution: str = "Wiktionary contributors",
        license: str = "CC BY-SA 4.0/GFDL",
        preserve_raw: bool = True,
        strict: bool = True,
    ):
        self.language_path = Path(language_path)
        self.english_path = Path(english_path) if english_path else self.language_path
        self.language = language.casefold().strip()
        self.edition = edition
        self.dump_revision = dump_revision
        self.attribution = attribution
        self.license = license
        self.preserve_raw = preserve_raw
        self.strict = strict

    def load(self, language_code: str, direction: str) -> list[DictionaryEntry]:
        if language_code != self.language:
            raise ConfigurationError(
                f"Provider {self.name!r} contains {self.language!r}, not requested language {language_code!r}"
            )
        if language_code not in _WIKTIONARY_LANGUAGE_CODES:
            raise ConfigurationError(f"No Wiktionary code mapping is configured for {language_code!r}")
        reverse = direction.startswith("eng-to-")
        path = self.english_path if reverse else self.language_path
        if not path.is_file():
            raise DataLoadError(f"Wiktextract JSONL file does not exist: {path}")

        entries: list[DictionaryEntry] = []
        errors: list[str] = []
        for line_number, record, error in self._records(path):
            if error:
                errors.append(error)
                continue
            if reverse:
                entries.extend(self._english_entries(record, path, line_number))
            else:
                entries.extend(self._language_entries(record, path, line_number))
        if errors and self.strict:
            raise DataLoadError(f"Rejected {len(errors)} lines from {path.name!r}; first error: {errors[0]}")
        return entries

    def _records(self, path: Path):
        opener = gzip.open if path.suffix.casefold() == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise TypeError("JSON value is not an object")
                except (json.JSONDecodeError, TypeError) as exc:
                    yield line_number, {}, f"line {line_number}: {exc}"
                    continue
                yield line_number, record, None

    def _language_entries(self, record: dict[str, Any], path: Path, line_number: int) -> list[DictionaryEntry]:
        if record.get("lang_code") not in _WIKTIONARY_LANGUAGE_CODES[self.language]:
            return []
        word = str(record.get("word") or "").strip()
        if not word:
            return []
        entries: list[DictionaryEntry] = []
        for sense_number, sense in enumerate(record.get("senses") or [], start=1):
            glosses = [str(value).strip() for value in sense.get("glosses") or [] if str(value).strip()]
            if not glosses:
                continue
            definition = glosses[-1]
            examples = [
                str(example.get("text") or "").strip()
                for example in sense.get("examples") or []
                if str(example.get("text") or "").strip()
            ]
            provenance = self._provenance(path, line_number, word)
            metadata = {
                "provider": self.name,
                "provenance": provenance,
                "wiktextract_sense": sense,
            }
            if self.preserve_raw:
                metadata["raw"] = record
            entries.append(
                DictionaryEntry(
                    entry_id=self._entry_id(record, line_number, sense_number),
                    word=word,
                    language=self.language,
                    target_language="eng",
                    part_of_speech=str(record.get("pos") or "").strip() or None,
                    definition=definition,
                    examples=examples,
                    source=self.name,
                    audit_status="external_community_source_unreviewed",
                    metadata=metadata,
                )
            )
        return entries

    def _english_entries(self, record: dict[str, Any], path: Path, line_number: int) -> list[DictionaryEntry]:
        if record.get("lang_code") not in {"en", "eng"}:
            return []
        word = str(record.get("word") or "").strip()
        if not word:
            return []
        target_codes = _WIKTIONARY_LANGUAGE_CODES[self.language]
        raw_candidates = list(record.get("translations") or [])
        for sense in record.get("senses") or []:
            raw_candidates.extend(sense.get("translations") or [])

        candidates: list[Translation] = []
        seen: set[tuple[str, str, str]] = set()
        for candidate in raw_candidates:
            if (candidate.get("lang_code") or candidate.get("code")) not in target_codes:
                continue
            translated = str(candidate.get("word") or "").strip()
            if not translated:
                continue
            context = str(candidate.get("sense") or candidate.get("note") or "").strip()
            key = (translated, context, str(candidate.get("roman") or ""))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                Translation(
                    text=translated,
                    language=self.language,
                    context=context or None,
                    metadata=candidate,
                )
            )
        if not candidates:
            return []

        provenance = self._provenance(path, line_number, word)
        metadata = {"provider": self.name, "provenance": provenance}
        if self.preserve_raw:
            metadata["raw"] = record
        return [
            DictionaryEntry(
                entry_id=self._entry_id(record, line_number, 0),
                word=word,
                language="eng",
                target_language=self.language,
                part_of_speech=str(record.get("pos") or "").strip() or None,
                definition="; ".join(dict.fromkeys(candidate.text for candidate in candidates)),
                translations=candidates,
                source=self.name,
                audit_status="external_community_source_unreviewed",
                metadata=metadata,
            )
        ]

    def _provenance(self, path: Path, line_number: int, word: str) -> dict[str, Any]:
        return {
            "provider": self.name,
            "edition": self.edition,
            "dump_revision": self.dump_revision,
            "file": path.name,
            "line": line_number,
            "wiktionary_word": word,
            "attribution": self.attribution,
            "license": self.license,
        }

    def _entry_id(self, record: dict[str, Any], line_number: int, sense_number: int) -> str:
        fingerprint = json.dumps(
            {
                "edition": self.edition,
                "revision": self.dump_revision,
                "line": line_number,
                "sense": sense_number,
                "word": record.get("word"),
                "lang_code": record.get("lang_code"),
                "pos": record.get("pos"),
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode()
        return f"wiktionary:{hashlib.sha256(fingerprint).hexdigest()[:20]}"
