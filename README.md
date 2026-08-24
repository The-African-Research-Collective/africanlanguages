# africanlanguages

## Setup

You'll need to [install uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods).

* Install `africanlanguages` by running `uv sync`

* Run `pre-commit install`

## Dictionary lookup

The dictionary interface uses the audited, versioned configurations in
[`taresco/afri-dict`](https://huggingface.co/datasets/taresco/afri-dict). The
first load downloads and caches a configuration; later loads reuse that cache.

```python
from africanlanguages.dictionary import Dictionary

# English lookup with source-backed Yoruba candidates
yoruba = Dictionary("yor", direction="english")
results = yoruba.lookup("strip naked")
print([translation.text for translation in results[0].translations])

# Yoruba-to-English, prefix search, and batch lookup
forward = Dictionary("yor")
forward.prefix("ab", limit=20)
forward.lookup_many(["àbà", "àbá"])
forward.metadata()

# Require an already-cached copy and make no network request
cached = Dictionary("yor", direction="english", offline=True)
```

`direction="language"` (the default) always means African-language headwords
with English results. `direction="english"` always means English headwords
with African-language results, even when the historical source book was
organized in the opposite direction. Reverse indexes are built only from
explicit translation candidates; explanatory definition prose is never
silently tokenized into mappings.

`Dictionary.languages()` lists the Hausa, Igbo, Swahili, and Yoruba
configurations. Exact lookup is Unicode- and case-normalized and can treat
historical hyphens as modern spaces. Results retain provenance, review flags,
source forms, and the complete canonical object in `entry.metadata`.

These are source-audited historical dictionaries, not automatic authorities
for contemporary spelling, dialect, register, or translation quality.

### Use another bilingual source

External mappings do not need to be added to Afri-Dict. A CSV or TSV with one
attested mapping per row can be queried in both directions and combined with
Afri-Dict while keeping source attribution attached to every result.

```python
from africanlanguages.dictionary import DelimitedFileProvider, Dictionary

igbo_source = DelimitedFileProvider(
    "igbo-english.tsv",
    language="ibo",
    source_column="igbo",
    english_column="english",
    name="community-igbo",
    attribution="Community Igbo lexicon",
    license="CC BY 4.0",
)

# Provider order is lookup-precedence order; matching results retain `source`.
igbo = Dictionary("ibo", providers=["afridict", igbo_source])
igbo.lookup("ụlọ")

english = Dictionary("ibo", direction="english", providers=[igbo_source])
english.lookup("house")
```

The provider does not derive mappings from explanatory prose or split a cell
into guessed translations. Raw rows, line numbers, attribution, and licence
metadata remain available through `entry.metadata` and `entry.provenance`.

Downloaded [FreeDict](https://freedict.org/downloads/) TEI sources can be used
directly without conversion or inclusion in the package:

```python
from africanlanguages.dictionary import Dictionary, FreeDictProvider

freedict = FreeDictProvider(
    "swa-eng.tei",
    language="swh",
    license="see the TEI header",
)

Dictionary("swh", providers=[freedict]).lookup("nyumba")
Dictionary("swh", direction="english", providers=[freedict]).lookup("house")
```

Filtered [Wiktextract](https://github.com/tatuylonen/wiktextract) JSONL and
JSONL.GZ exports are also supported. Supply native-language records for
language-to-English definitions and English records containing explicit
Wiktionary translations for English-to-language lookup:

```python
from africanlanguages.dictionary import Dictionary, WiktextractProvider

wiktionary = WiktextractProvider(
    "yoruba-entries.jsonl.gz",
    english_path="english-entries-with-yoruba-translations.jsonl.gz",
    language="yor",
    dump_revision="2026-08-01",
)

Dictionary("yor", providers=[wiktionary]).lookup("ilé")
Dictionary("yor", direction="english", providers=[wiktionary]).lookup("house")
```

For native headwords, Wiktionary glosses remain definitions and are not
pretended to be word-for-word translations. The reverse direction indexes
only structured `translations` objects from English entries. This prevents a
definition such as “a building in which people live” from becoming a set of
fabricated reverse-lookup keys.

## Notes on Dependencies

- [Extra dependency](https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies): published along with the package.
- [Dependency group](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups): only used during development.
