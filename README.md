# babygruut

A tokenizer, text cleaner, and [IPA](https://en.wikipedia.org/wiki/International_Phonetic_Alphabet) phonemizer for several human languages that supports [SSML](#ssml).

**babygruut** is a production fork of [gruut](https://github.com/rhasspy/gruut) (now archived). It retains full compatibility with the original API while adding support for loading pronunciation lexicons from a remote [Turso](https://turso.tech/) (libSQL) database instead of only from bundled local SQLite files.

---

## What's Different from Original gruut

| | gruut (original) | babygruut |
|---|---|---|
| Package name | `gruut` | `babygruut` |
| Lexicon source | Bundled local `.db` files only | Remote Turso DB (with local SQLite fallback) |
| English language pack | `gruut_lang_en ~=2.0.0` | `babygruut-lang-en ==2.0.2` (updated POS model) |
| Luxembourgish (`lb`) | Not included | Included |
| New dependency | — | `libsql-client ~=0.3.1` |
| Upstream status | Archived Oct 2025 | Actively maintained |

The core text processing pipeline — tokenization, verbalization, SSML handling, POS tagging, G2P fallback, and homograph resolution — is **unchanged**. The only architectural difference is where the pronunciation data comes from.

---

## How the Turso Integration Works

On initialization, babygruut connects to the configured Turso database and downloads the entire lexicon table into an **in-memory SQLite database**. From that point on, all phoneme lookups are served from memory — there are no per-word network requests at inference time.

```
Startup:
  Turso (remote libSQL) ──batch load──► in-memory SQLite ──► SqlitePhonemizer

Inference:
  word + POS role ──► in-memory SQLite lookup ──► IPA phonemes
                  └──► G2P model (if word not in lexicon)
```

The in-memory SQLite uses the same schema as the original gruut lexicon files:

```sql
CREATE TABLE word_phonemes (
    word       TEXT,
    phonemes   TEXT,
    pron_order INTEGER,
    role       TEXT
);
```

Because the lookup engine (`SqlitePhonemizer`) is shared between both paths, **homograph resolution works identically** whether the data came from Turso or a bundled local file — provided the `role` column is populated (see [Limitations](#limitations)).

If the Turso connection fails at startup, babygruut automatically falls back to the bundled local SQLite lexicon for the requested language.

---

## Setup

### Environment Variables

Export the following before running:

```sh
export TURSO_LEXICON_URL="libsql://your-database.turso.io"
export TURSO_LEXICON_AUTH_TOKEN="your-auth-token"
```

### Turso Database Schema

Your Turso table must match this schema:

```sql
CREATE TABLE your_table_name (
    word       TEXT,
    phonemes   TEXT,       -- space-separated IPA phonemes, e.g. "h ˈɛ l oʊ"
    pron_order INTEGER,    -- 0 = preferred pronunciation
    role       TEXT        -- POS role e.g. "gruut:VB", or "" for default
);
```

For homograph disambiguation (e.g., distinguishing "wound" as noun vs. verb), populate the `role` column with gruut-style POS tags. See [Word Roles](#word-roles) for the tag format. If `role` is left empty for all rows, the pronunciation with the lowest `pron_order` is always returned.

### Installation

```sh
pip install git+https://github.com/bookbot-hive/babygruut.git@turso_db
```

---

## Basic Usage

```python
from gruut import sentences

text = 'He wound it around the wound, saying "I read it was $10 to read."'

for sent in sentences(text, lang="en-us"):
    for word in sent:
        if word.phonemes:
            print(word.text, *word.phonemes)
```

Output:

```
He h ˈi
wound w ˈaʊ n d
it ˈɪ t
around ɚ ˈaʊ n d
the ð ə
wound w ˈu n d
, |
saying s ˈeɪ ɪ ŋ
I ˈaɪ
read ɹ ˈɛ d
it ˈɪ t
was w ə z
ten t ˈɛ n
dollars d ˈɑ l ɚ z
to t ə
read ɹ ˈi d
. ‖
```

Note that "wound" and "read" have different pronunciations depending on grammatical context — this works for English because the bundled `babygruut-lang-en` lexicon includes POS-keyed role data for ~1,150 homographs.

### With Turso Lexicon

Pass a `turso_config` dict to route phoneme lookups through your remote database:

```python
from gruut import sentences

turso_config = {
    "url": "libsql://your-database.turso.io",
    "auth_token": "your-auth-token",
    "table": "sw_phonemes",   # your table name
}

for sent in sentences(text, lang="sw", turso_config=turso_config):
    for word in sent:
        if word.phonemes:
            print(word.text, *word.phonemes)
```

The Turso table is loaded into memory on first use. If the connection fails, the language's bundled local lexicon is used as a fallback.

### SSML

```python
from gruut import sentences

ssml_text = """<?xml version="1.0" encoding="ISO-8859-1"?>
<speak version="1.1" xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.w3.org/2001/10/synthesis
                http://www.w3.org/TR/speech-synthesis11/synthesis.xsd"
    xml:lang="en-US">
<s>Today at 4pm, 2/1/2000.</s>
<s xml:lang="it">Un mese fà, 2/1/2000.</s>
</speak>"""

for sent in sentences(ssml_text, ssml=True):
    for word in sent:
        if word.phonemes:
            print(sent.idx, word.lang, word.text, *word.phonemes)
```

Output:

```
0 en-US Today t ə d ˈeɪ
0 en-US at ˈæ t
0 en-US four f ˈɔ ɹ
0 en-US P p ˈi
0 en-US M ˈɛ m
0 en-US , |
0 en-US February f ˈɛ b j u ˌɛ ɹ i
0 en-US first f ˈɚ s t
0 en-US , |
0 en-US two t ˈu
0 en-US thousand θ ˈaʊ z ə n d
0 en-US . ‖
1 it Un u n
1 it mese ˈm e s e
1 it fà f a
1 it , |
1 it due d j u
1 it gennaio d͡ʒ e n n ˈa j o
1 it duemila d u e ˈm i l a
1 it . ‖
```

---

## Limitations

**Startup cost.** The entire Turso table is downloaded into memory at initialization. For large lexicons this adds a one-time latency on first use (no per-request network cost after that).

**No live updates.** The in-memory cache is built once at startup. Changes pushed to the Turso database are not reflected until the process restarts.

**Homograph disambiguation requires role data.** POS-aware pronunciation selection only works when the `role` column in your Turso table is populated with gruut-style tags (e.g., `gruut:VB`, `gruut:NN`). If all roles are empty, the lowest `pron_order` pronunciation is always returned regardless of grammatical context. The bundled English lexicon already has role data; Turso-sourced lexicons need to include it explicitly.

**G2P fallback ignores role.** When a word is not found in the lexicon, the grapheme-to-phoneme (G2P) CRF model is used to guess a pronunciation. The G2P model does not receive the POS role, so it cannot disambiguate homographs for out-of-vocabulary words.

**Memory usage scales with lexicon size.** All rows are held in an in-memory SQLite instance for the lifetime of the process. Very large lexicons (hundreds of thousands of entries) will increase RAM usage proportionally.

**Single table per language.** Each `turso_config` maps to one table. If you need multiple languages served from Turso, create a separate `turso_config` per language and pass it when calling `sentences()` for that language.

---

## Supported Languages

| Language | Code |
|---|---|
| Arabic | `ar` |
| Czech | `cs` or `cs-cz` |
| German | `de` or `de-de` |
| English | `en` or `en-us` |
| Spanish | `es` or `es-es` |
| Farsi/Persian | `fa` |
| French | `fr` or `fr-fr` |
| Italian | `it` or `it-it` |
| Luxembourgish | `lb` |
| Dutch | `nl` |
| Russian | `ru` or `ru-ru` |
| Swedish | `sv` or `sv-se` |
| Swahili | `sw` |

---

## Dependencies

* Python 3.7 or higher
* Linux (tested on Debian Bullseye)
* [num2words fork](https://github.com/rhasspy/num2words) and [Babel](https://pypi.org/project/Babel/) — currency/number handling
* [gruut-ipa](https://github.com/rhasspy/gruut-ipa) — IPA phoneme manipulation
* [pycrfsuite](https://github.com/scrapinghub/python-crfsuite) — POS tagging and G2P models
* [pydateparser](https://github.com/GLibAi/pydateparser) — date parsing for multiple languages
* [libsql-client](https://pypi.org/project/libsql-client/) `~=0.3.1` — Turso/libSQL database client *(new)*

---

## Numbers, Dates, and More

`gruut` can automatically verbalize numbers, dates, and other expressions in a locale-aware manner, so "1/1/2020" may be interpreted as "M/D/Y" or "D/M/Y" depending on the sentence's language.

The following expression types are automatically expanded:

* **Numbers** — "123" → "one hundred and twenty three" (`verbalize_numbers=False` to disable)
* **Dates** — "1/1/2020" → "January first, twenty twenty" (`verbalize_dates=False` to disable)
* **Currency** — "$10" → "ten dollars" (`verbalize_currency=False` to disable)
* **Times** — "12:01am" → "twelve oh one A M" (English only; `verbalize_times=False` to disable)

---

## Command-Line Usage

```sh
echo 'This, right here, is some "RAW" text!' \
   | gruut --language en-us \
   | jq --raw-output '.words[].text'
```

Output:

```
This
,
right
here
,
is
some
"
RAW
"
text
!
```

Full JSON output per sentence:

```sh
gruut --language en-us 'More text.' | jq .
```

Each word in the output includes:

* `idx` — zero-based index of the word in the sentence
* `sent_idx` — zero-based index of the sentence in the input
* `pos` — part of speech tag (if available)
* `phonemes` — list of IPA phonemes (if available)
* `is_minor_break` — `true` for commas, semicolons, etc.
* `is_major_break` — `true` for periods, question marks, etc.
* `is_spoken` — `true` if not a break or punctuation

See `python3 -m gruut <LANGUAGE> --help` for all options.

---

## SSML

A subset of [SSML](https://www.w3.org/TR/speech-synthesis11/) is supported:

* `<speak>` — wrap around SSML text (`lang` attribute sets document language)
* `<p>` — paragraph (`lang` attribute)
* `<s>` — sentence, disables automatic sentence breaking (`lang` attribute)
* `<w>` / `<token>` — word, disables automatic tokenization (`lang`, `role` attributes)
* `<lang lang="...">` — set language for inner text
* `<voice name="...">` — set voice of inner text
* `<say-as interpret-as="">` — force interpretation (`spell-out`, `date`, `number`, `time`, `currency`)
* `<break time="">` — pause (`123s` or `123ms`)
* `<mark name="">` — user-defined mark
* `<sub alias="">` — substitute alias for inner text
* `<phoneme ph="...">` — supply phonemes directly for inner text
* `<lexicon id="...">` — inline or external pronunciation lexicon
* `<lookup ref="...">` — use a named pronunciation lexicon for child elements

### Word Roles

During phonemization, word roles disambiguate pronunciations. Unless manually specified, a word's role is derived from its POS tag as `gruut:<TAG>`. For initialisms and `spell-out`, the role `gruut:letter` is used.

For `en-us`, the POS tagger produces these roles:

| Role | Meaning |
|---|---|
| `gruut:CD` | number |
| `gruut:DT` | determiner |
| `gruut:IN` | preposition or subordinating conjunction |
| `gruut:JJ` | adjective |
| `gruut:NN` | noun |
| `gruut:PRP` | personal pronoun |
| `gruut:RB` | adverb |
| `gruut:VB` | verb (present) |
| `gruut:VBD` | verb (past tense) |

When using a Turso lexicon, populate the `role` column with these same values to enable context-aware pronunciation for homographs.

### Inline Lexicons

Inline [pronunciation lexicons](https://www.w3.org/TR/2008/REC-pronunciation-lexicon-20081014/) are supported via `<lexicon>` and `<lookup>`. gruut extends the SSML standard by allowing lexicons to be defined inline (no `uri` required) and by allowing the `id` attribute to be omitted for a "default" lexicon that applies without a `<lookup>` tag.

```xml
<?xml version="1.0"?>
<speak version="1.1"
       xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.w3.org/2001/10/synthesis
                 http://www.w3.org/TR/speech-synthesis11/synthesis.xsd"
       xml:lang="en-US">

  <lexicon xml:id="test" alphabet="ipa">
    <lexeme>
      <grapheme>tomato</grapheme>
      <phoneme>t ə m ˈɑ t oʊ</phoneme>
    </lexeme>
    <lexeme>
      <grapheme role="fake-role">tomato</grapheme>
      <phoneme>t ə m ˈi t oʊ</phoneme>
    </lexeme>
  </lexicon>

  <w>tomato</w>
  <lookup ref="test">
    <w>tomato</w>
    <w role="fake-role">tomato</w>
  </lookup>
</speak>
```

The first "tomato" uses the language lexicon. Within the `<lookup>` scope, the second and third use the inline lexicon — the third selects the role-specific pronunciation.

---

## Intended Audience

babygruut is useful for transforming raw text into phonetic pronunciations for TTS pipelines. It looks up words in a pre-built lexicon (local or remote via Turso) and falls back to a pre-trained grapheme-to-phoneme model for unknown words.

For each supported language, babygruut includes:

* A word pronunciation lexicon built from open source data (see [pron_dict](https://github.com/Kyubyong/pron_dictionaries))
* A pre-trained G2P model for guessing pronunciations of out-of-vocabulary words

Some languages also include:

* A pre-trained part of speech tagger (see [Universal Dependencies](https://universaldependencies.org/))
