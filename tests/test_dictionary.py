"""Behavior-focused tests for the public dictionary interface."""

import gzip
import json

import pytest
from pydantic import ValidationError

from africanlanguages.core.exceptions import ConfigurationError, DataLoadError
from africanlanguages.dictionary import (
    DelimitedFileProvider,
    Dictionary,
    DictionaryEntry,
    DictionaryProvider,
    DictionaryQuery,
    FreeDictProvider,
    Translation,
    WiktextractProvider,
    normalize_text,
)
from africanlanguages.dictionary import loader as dictionary_loader


@pytest.fixture
def sample_entries():
    return [
        DictionaryEntry(
            entry_id="yor:1",
            word="bọ-laṣọ",
            language="yor",
            target_language="eng",
            part_of_speech="verb",
            definition="to strip naked",
            audit_status="native_reviewed",
            metadata={"provenance": {"page": 42}, "audit": {"reviewed": True}},
        ),
        DictionaryEntry(
            entry_id="yor:2",
            word="bọ bata",
            language="yor",
            target_language="eng",
            definition="to take off shoes",
        ),
        DictionaryEntry(word="àbà", language="yor", definition="a mark"),
    ]


def test_models_preserve_evidence():
    translation = Translation(
        text="bọ laṣọ",
        language="yor",
        source_form="bọ-laṣọ",
        review_flags=["native_reviewed"],
        metadata={"candidate_id": "candidate:1"},
    )
    entry = DictionaryEntry(
        word="strip naked",
        language="eng",
        target_language="yor",
        translations=[translation],
        metadata={"provenance": {"printed_page": 42}},
    )
    assert entry.translations[0].source_form == "bọ-laṣọ"
    assert entry.provenance == {"printed_page": 42}


def test_model_required_fields():
    with pytest.raises(ValidationError):
        DictionaryEntry(word="test", language="")
    with pytest.raises(ValidationError):
        Translation(text="", language="yor")


def test_normalization_aware_exact_lookup(sample_entries):
    query = DictionaryQuery(sample_entries)
    assert query.search("BỌ-LAṢỌ")[0].entry_id == "yor:1"
    assert query.search("bọ laṣọ")[0].entry_id == "yor:1"
    assert query.search("bọ laṣọ", normalization_aware=False) == []
    assert normalize_text("  BỌ‐LAṢỌ  ", separator_insensitive=True) == "bọ laṣọ"


def test_prefix_fuzzy_and_batch_lookup(sample_entries):
    query = DictionaryQuery(sample_entries)
    assert [entry.word for entry in query.prefix("bọ", limit=2)] == ["bọ bata", "bọ-laṣọ"]
    assert query.search("aba", fuzzy=True, threshold=0.5)[0].word == "àbà"
    batch = query.lookup_many(["bọ laṣọ", "missing"])
    assert batch["bọ laṣọ"][0].entry_id == "yor:1"
    assert batch["missing"] == []


def test_dictionary_high_level_interface(sample_entries):
    dictionary = Dictionary("Yoruba", direction="english", entries=sample_entries)
    assert dictionary.lookup("bọ laṣọ")[0].entry_id == "yor:1"
    assert dictionary.prefix("bọ", limit=1)[0].word == "bọ bata"
    assert dictionary.lookup_many(["àbà"])["àbà"][0].word == "àbà"
    assert dictionary.define("bọ bata") == ["to take off shoes"]
    metadata = dictionary.metadata()
    assert metadata.config_name == "en_yor_v1"
    assert metadata.entry_count == 3
    assert {item.language_code for item in Dictionary.languages()} == {"hau", "ibo", "swh", "yor"}


def test_config_resolution_rejects_invalid_values():
    with pytest.raises(ConfigurationError):
        Dictionary("zul", entries=[])
    with pytest.raises(ConfigurationError):
        Dictionary("yor", direction="sideways", entries=[])
    with pytest.raises(ConfigurationError):
        Dictionary("yor", config_name="ibo_v1", entries=[])


def test_direction_resolution_uses_headword_language_not_source_book_direction():
    assert dictionary_loader.resolve_dictionary_config("swh", "language") == (
        "swh",
        "en_swh_v1",
        "swh-to-eng",
    )
    assert dictionary_loader.resolve_dictionary_config("swh", "english") == (
        "swh",
        "en_swh_v1",
        "eng-to-swh",
    )


def test_loader_selects_versioned_config_and_parses_canonical_object(monkeypatch):
    calls = []
    canonical = {
        "english": "strip naked",
        "entry_id": "yor:reverse:1",
        "language": "yor",
        "translations": [
            {
                "target_form": "bọ laṣọ",
                "target_source_form": "bọ-laṣọ",
                "review_flags": ["native_reviewed"],
            }
        ],
        "provenance": {"printed_page": 42},
        "review": {"native_speaker_review_required": False},
    }
    rows = [
        {
            "entry_id": "yor:reverse:1",
            "language": "eng",
            "target_language": "yor",
            "word": "strip naked",
            "pos": "verb",
            "definition": "bọ laṣọ",
            "audit_status": "source_audited_historical_candidate",
            "entry_json": json.dumps(canonical),
        }
    ]

    def fake_load_dataset(*args, **kwargs):
        calls.append((args, kwargs))
        return rows

    monkeypatch.setattr(dictionary_loader, "load_dataset", fake_load_dataset)
    entries = dictionary_loader.load_dictionary("yo", direction="english")
    assert calls[0][0] == ("taresco/afri-dict",)
    assert calls[0][1]["name"] == "en_yor_v1"
    assert calls[0][1]["revision"] == dictionary_loader.AFRI_DICT_REVISION
    assert entries[0].translations[0].text == "bọ laṣọ"
    assert entries[0].translations[0].source_form == "bọ-laṣọ"
    assert entries[0].provenance == {"printed_page": 42}


def test_loader_is_strict_by_default(monkeypatch):
    monkeypatch.setattr(
        dictionary_loader,
        "load_dataset",
        lambda *args, **kwargs: [{"word": "broken", "language": "eng", "entry_json": "{"}],
    )
    with pytest.raises(DataLoadError, match="Rejected 1 rows"):
        dictionary_loader.load_dictionary("hau")


def test_loader_safely_inverts_explicit_candidates_for_language_lookup(monkeypatch):
    canonical = {
        "english": "house",
        "entry_id": "swa:reverse:house",
        "language": "swa",
        "translations": [{"target_form": "nyumba", "target_source_form": "nyumba"}],
    }
    monkeypatch.setattr(
        dictionary_loader,
        "load_dataset",
        lambda *args, **kwargs: [
            {
                "entry_id": "swa:reverse:house",
                "language": "eng",
                "target_language": "swh",
                "word": "house",
                "definition": "nyumba",
                "entry_json": json.dumps(canonical),
            }
        ],
    )
    entries = dictionary_loader.load_dictionary("swh", direction="language")
    assert entries[0].word == "nyumba"
    assert entries[0].language == "swh"
    assert entries[0].definition == "house"
    assert entries[0].translations[0].text == "house"
    assert entries[0].metadata["inverted_from"]["entry_id"] == "swa:reverse:house"


def test_loader_refuses_to_reverse_definition_prose(monkeypatch):
    monkeypatch.setattr(
        dictionary_loader,
        "load_dataset",
        lambda *args, **kwargs: [
            {
                "entry_id": "eng:1",
                "language": "eng",
                "target_language": "swh",
                "word": "house",
                "definition": "a building in which people live",
            }
        ],
    )
    with pytest.raises(DataLoadError, match="no explicit translation candidates"):
        dictionary_loader.load_dictionary("swh", direction="language")


def test_offline_loader_uses_local_only_download_config(monkeypatch):
    captured = {}

    def fake_load_dataset(*args, **kwargs):
        captured.update(kwargs)
        return [{"word": "àbà", "language": "yor", "definition": "a mark"}]

    monkeypatch.setattr(dictionary_loader, "load_dataset", fake_load_dataset)
    dictionary_loader.load_dictionary("yor", offline=True)
    assert captured["download_config"].local_files_only is True


def test_delimited_provider_supports_both_directions_and_provenance(tmp_path):
    source = tmp_path / "igbo.tsv"
    source.write_text(
        "igbo\tenglish\tpos\tnote\nụlọ\thouse\tnoun\tbuilding or home\nụlọ\thome\tnoun\tdwelling\n",
        encoding="utf-8",
    )
    provider = DelimitedFileProvider(
        source,
        language="ibo",
        source_column="igbo",
        english_column="english",
        part_of_speech_column="pos",
        context_column="note",
        name="community-igbo",
        attribution="Community lexicon",
        license="CC BY 4.0",
    )

    forward = Dictionary("ibo", providers=[provider])
    assert [entry.definition for entry in forward.lookup("ụlọ")] == ["house", "home"]
    assert forward.lookup("ụlọ")[0].translations[0].context == "building or home"
    assert forward.lookup("ụlọ")[0].provenance == {
        "provider": "community-igbo",
        "file": "igbo.tsv",
        "line": 2,
        "attribution": "Community lexicon",
        "license": "CC BY 4.0",
    }

    reverse = Dictionary("ibo", direction="english", providers=[provider])
    result = reverse.lookup("HOME")[0]
    assert result.translations[0].text == "ụlọ"
    assert result.source == "community-igbo"
    assert reverse.metadata().providers == ["community-igbo"]


def test_delimited_provider_rejects_missing_or_malformed_rows(tmp_path):
    missing_column = tmp_path / "missing.csv"
    missing_column.write_text("igbo,gloss\nụlọ,house\n", encoding="utf-8")
    provider = DelimitedFileProvider(
        missing_column,
        language="ibo",
        source_column="igbo",
        english_column="english",
    )
    with pytest.raises(DataLoadError, match="missing columns: english"):
        Dictionary("ibo", providers=[provider])

    malformed = tmp_path / "malformed.csv"
    malformed.write_text("igbo,english\nụlọ,house\n,home\n", encoding="utf-8")
    provider = DelimitedFileProvider(
        malformed,
        language="ibo",
        source_column="igbo",
        english_column="english",
    )
    with pytest.raises(DataLoadError, match="Rejected 1 rows"):
        Dictionary("ibo", providers=[provider])


def test_multiple_providers_preserve_precedence_and_attribution():
    class StubProvider(DictionaryProvider):
        def __init__(self, name, meaning):
            self.name = name
            self.meaning = meaning

        def load(self, language_code, direction):
            return [
                DictionaryEntry(
                    word="ụlọ",
                    language="ibo",
                    target_language="eng",
                    definition=self.meaning,
                    source=self.name,
                )
            ]

    dictionary = Dictionary(
        "ibo",
        providers=[StubProvider("first", "house"), StubProvider("second", "home")],
    )
    assert [entry.definition for entry in dictionary.lookup("ụlọ")] == ["house", "home"]
    assert dictionary.provider_names == ["first", "second"]


def test_dictionary_rejects_entries_and_providers_together(sample_entries):
    with pytest.raises(ValueError, match="either entries or providers"):
        Dictionary("yor", entries=sample_entries, providers=[])


def test_freedict_tei_provider_supports_both_directions(tmp_path):
    source = tmp_path / "swa-eng.tei"
    source.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text><body>
    <entry xml:id="nyumba">
      <form><orth>nyumba</orth></form>
      <gramGrp><pos>n</pos></gramGrp>
      <sense>
        <cit type="trans"><quote>house</quote></cit>
        <cit type="trans"><quote>home</quote></cit>
      </sense>
    </entry>
    <entry xml:id="cross-reference-only"><form><orth>maskani</orth></form></entry>
  </body></text>
</TEI>
""",
        encoding="utf-8",
    )
    provider = FreeDictProvider(source, language="swh", license="GPL-2.0-or-later")

    forward = Dictionary("swh", providers=[provider])
    assert [entry.definition for entry in forward.lookup("nyumba")] == ["house", "home"]
    assert forward.lookup("maskani") == []
    assert forward.lookup("nyumba")[0].provenance["tei_entry_id"] == "nyumba"

    reverse = Dictionary("swh", direction="english", providers=[provider])
    assert reverse.lookup("home")[0].translations[0].text == "nyumba"


def test_freedict_english_source_orientation(tmp_path):
    source = tmp_path / "eng-swa.tei"
    source.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><entry xml:id="house">
<form><orth>house</orth></form><sense><cit type="trans"><quote>nyumba</quote></cit></sense>
</entry></body></text></TEI>""",
        encoding="utf-8",
    )
    provider = FreeDictProvider(source, language="swh", source_is_english=True)
    assert Dictionary("swh", providers=[provider]).lookup("nyumba")[0].definition == "house"
    assert Dictionary("swh", direction="english", providers=[provider]).lookup("house")[0].definition == "nyumba"


def test_wiktextract_provider_uses_glosses_and_explicit_translations(tmp_path):
    language_path = tmp_path / "yoruba.jsonl.gz"
    language_record = {
        "word": "ilé",
        "lang": "Yoruba",
        "lang_code": "yo",
        "pos": "noun",
        "senses": [
            {
                "glosses": ["house"],
                "examples": [{"text": "Ilé mi ni èyí.", "translation": "This is my house."}],
            },
            {"glosses": ["home"]},
        ],
    }
    with gzip.open(language_path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(language_record, ensure_ascii=False) + "\n")

    english_path = tmp_path / "english.jsonl"
    english_records = [
        {
            "word": "house",
            "lang": "English",
            "lang_code": "en",
            "pos": "noun",
            "translations": [
                {"word": "ilé", "lang_code": "yo", "sense": "building or dwelling"},
                {"word": "maison", "lang_code": "fr"},
                {"word": "ilé", "lang_code": "yo", "sense": "building or dwelling"},
            ],
        },
        {
            "word": "dwelling",
            "lang_code": "en",
            "pos": "noun",
            "senses": [{"glosses": ["a place where someone lives"]}],
        },
    ]
    english_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in english_records),
        encoding="utf-8",
    )
    provider = WiktextractProvider(
        language_path,
        english_path=english_path,
        language="yor",
        dump_revision="2026-08-01",
    )

    language_dictionary = Dictionary("yor", providers=[provider])
    results = language_dictionary.lookup("ilé")
    assert [entry.definition for entry in results] == ["house", "home"]
    assert results[0].examples == ["Ilé mi ni èyí."]
    assert results[0].translations == []
    assert results[0].metadata["raw"] == language_record
    assert results[0].provenance["dump_revision"] == "2026-08-01"

    english_dictionary = Dictionary("yor", direction="english", providers=[provider])
    result = english_dictionary.lookup("house")[0]
    assert result.definition == "ilé"
    assert [translation.text for translation in result.translations] == ["ilé"]
    assert result.translations[0].context == "building or dwelling"
    assert english_dictionary.lookup("dwelling") == []


def test_wiktextract_provider_rejects_malformed_jsonl(tmp_path):
    path = tmp_path / "broken.jsonl"
    path.write_text('{"word": "ilé"}\nnot-json\n', encoding="utf-8")
    provider = WiktextractProvider(path, language="yor")
    with pytest.raises(DataLoadError, match="Rejected 1 lines"):
        Dictionary("yor", providers=[provider])


def test_wiktextract_provider_can_omit_raw_records(tmp_path):
    path = tmp_path / "igbo.jsonl"
    path.write_text(
        json.dumps(
            {
                "word": "ụlọ",
                "lang_code": "ig",
                "pos": "noun",
                "senses": [{"glosses": ["house"]}],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    provider = WiktextractProvider(path, language="ibo", preserve_raw=False)
    assert "raw" not in Dictionary("ibo", providers=[provider]).lookup("ụlọ")[0].metadata
