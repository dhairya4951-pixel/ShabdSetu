# ShabdSetu (शब्दसेतु)

**A bilingual dictionary that helps people find Indian-language words using Devanagari, IAST, and familiar Romanised spellings.**

ShabdSetu is a Django-based dictionary application developed for the **Garuda Prakashan × Rishihood — Track 3: Dictionary App** selection assignment. The goal is to make dictionary lookup accessible to people who may know a word's pronunciation but prefer typing with a standard Roman/English keyboard.

> **Dataset note:** The first 10 records are the starter data supplied in the assignment. The additional 40 records (IDs 11–50) were drafted with AI assistance and must be checked against reliable linguistic references before being marked verified. Do not treat AI-generated entries as authoritative by default.

## Features

### Dictionary experience

- Search using Devanagari headwords.
- Search using IAST transliteration and common Romanised spellings.
- Normalize common input differences such as case and spacing.
- Support partial matching and typo suggestions where implemented.
- Display dictionary entry details: headword, IAST transliteration, spelling variants, part of speech, meanings, and example sentence.
- Show a clear no-results state.
- Responsive layout for desktop and mobile screens.

### Content management

- Django ORM models for dictionary entries, Romanised variants, and meanings.
- Django Admin interface for staff maintenance.
- Custom staff-facing management interface at `/manage/` (if enabled in this deployment).
- Entry verification and source metadata fields (where present in the current model implementation).

**Important:** Update this feature list if any item is not present or working in the final repository. In particular, describe fuzzy matching as a suggestion mechanism, not guaranteed linguistic understanding.

## Technology

- Python
- Django
- SQLite for local development (confirm the production database separately)
- Django Templates
- HTML, CSS, and vanilla JavaScript
- Transliteration and fuzzy-matching libraries, if present in `requirements.txt`

See `requirements.txt` for the exact dependencies and versions used by this repository.

## Project structure

The project uses a Django project package and a `dictionary` application. The exact package names may differ; inspect the repository if adapting these instructions.

```text
ShabdSetu/
├── manage.py
├── requirements.txt
├── README.md
├── AI_LOG.md
├── <django_project>/
├── dictionary/
│   ├── models.py
│   ├── admin.py
│   ├── views.py
│   ├── search.py
│   ├── urls.py
│   ├── data/
│   │   └── entries.json
│   ├── management/
│   │   └── commands/
│   │       └── import_dictionary.py
│   └── templates/
└── static/
```

If the actual folder layout differs, keep the repository's real structure and update this tree.

## Getting started

### 1. Clone the repository

```bash
git clone <PUBLIC_GITHUB_REPOSITORY_URL>
cd <REPOSITORY_DIRECTORY>
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file only if the project uses one. Set the Django secret key, debug setting, allowed hosts, and database configuration according to the project's settings. Never commit production secrets or real credentials.

For local development, follow the defaults documented in the project's settings. Do not use `DEBUG=True` in production.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Import dictionary data

The working dataset is intended to be maintained in the existing JSON file:

```text
dictionary/data/entries.json
```

Keep the original 10 starter records and append records 11–50 to that same file. Do not replace the starter records. Ensure IDs/headwords are unique and preserve the assignment's field names:

- `id`
- `headword`
- `transliteration`
- `romanised`
- `pos`
- `meanings`
- `example`

Run the project's importer:

```bash
python manage.py import_dictionary
```

The command above assumes the repository contains the `import_dictionary` management command and that it reads `dictionary/data/entries.json` by default. If the implemented command or file path differs, use the actual command shown by the project and update this section.

After importing, confirm the database contains at least 50 unique entries. Run the importer a second time and check that it does not create duplicates or overwrite edits made in the admin interface.

### 7. Create an administrator account

```bash
python manage.py createsuperuser
```

Use a strong password. Do not put credentials in the repository or demo recording.

### 8. Run the development server

```bash
python manage.py runserver
```

Open the local URL printed by Django, normally `http://127.0.0.1:8000/`.

- Public dictionary: `/`
- Custom management interface: `/manage/` (staff access required, if configured)
- Django Admin: `/admin/`

## How search works

Search is intended to combine several candidate-generation and ranking steps:

1. Exact Devanagari headword matching.
2. Exact match against stored Romanised variants.
3. IAST transliteration matching.
4. Unicode and case normalization.
5. Transliteration-based candidate matching for spellings not explicitly stored.
6. Prefix/partial matching.
7. Fuzzy suggestions for likely typos.

Exact matches should rank above weaker matches. Fuzzy results should be labelled as suggestions and should not be represented as certain dictionary matches. Romanised spellings are not standardized, so ambiguous inputs cannot always be resolved reliably.

Check `dictionary/search.py` for the actual implementation. This description should be edited if the shipped algorithm differs.

## Data model

The intended relational structure is:

- **DictionaryEntry:** one headword with IAST transliteration, part of speech, example, and optional source/verification metadata.
- **RomanisedVariant:** one alternative Roman spelling related to a dictionary entry.
- **Meaning:** one meaning related to a dictionary entry, with a position field to preserve display order.

This keeps the content editable through Django Admin while retaining JSON as the initial import format.

## Testing

Run Django's system check and test suite:

```bash
python manage.py check
python manage.py test
```

Before submitting, manually test at least:

- Devanagari: `शिक्षा`, `धर्म`.
- Romanised: `shiksha`, `dharma`, `prakriti`.
- IAST: `śikṣā`, `dharma`, `prakṛti`.
- Case and spacing variations.
- A spelling not explicitly present in the aliases.
- A partial query and a typo suggestion.
- A query with no match.
- Entry detail pages and all displayed fields.
- Staff-only access to `/manage/` and `/admin/`.
- Create, edit, and delete flows in the management interface.
- Narrow mobile widths and desktop layout.

Record actual test results in `AI_LOG.md`. Do not say the test suite passed unless it was run and passed.

## Data quality and attribution

The assignment supplied the original 10 starter records. The additional records were drafted with AI assistance. They should remain unverified until a human checks the Devanagari spelling, IAST, part of speech/gender, aliases, meanings, and example sentence against appropriate references.

Potential references for review include:

- Cologne Digital Sanskrit Dictionaries: https://www.sanskrit-lexicon.uni-koeln.de/
- Monier-Williams digital corpus: https://sanskrit-lexicon.github.io/MWS/
- Hindi Shabd-Sindhu: https://hindishabdsindhu.rajbhasha.gov.in/
- Hindi Shabdamitra (CFILT, IIT Bombay): https://www.cfilt.iitb.ac.in/hindishabdamitra/

These are reference resources, not a claim that every record has already been checked. If material is copied or adapted from a third-party dictionary, follow that source's licence and attribution requirements. Record the sources actually used for each verified entry.

## Trade-offs and known limitations

- The app prioritizes a focused dictionary experience over user accounts and social features.
- Romanised spellings vary by region and user habit; support is necessarily incomplete.
- Transliteration libraries cannot infer every informal spelling reliably.
- Fuzzy matching can produce false positives, especially for short queries.
- The initial vocabulary is limited to at least 50 entries and does not represent comprehensive Hindi or Sanskrit coverage.
- AI-assisted entries require human review before being marked verified.
- Offline support, bookmarks, recent searches, and word-of-the-day features are outside the initial P0 scope unless separately implemented.

## What I would build with two more weeks

1. Improve search using a documented transliteration policy, a larger reviewed alias set, and a benchmark of real Romanised queries.
2. Expand the dictionary with reviewed entries, provenance, and a repeatable editorial workflow.
3. Add user bookmarks and recent searches with appropriate privacy controls.
4. Improve automated tests for Unicode normalization, ambiguous input, ranking, and false-positive rates.
5. Add offline/PWA support only after confirming caching and data-update behaviour.
6. Improve accessibility and run usability tests with people who type Indian-language words in Roman script.

## Security notes

- Keep `SECRET_KEY`, database credentials, and deployment tokens out of Git.
- Set production `DEBUG=False` and configure `ALLOWED_HOSTS`.
- Use HTTPS in deployment.
- Restrict `/manage/` and `/admin/` to authorized staff.
- Keep CSRF protection enabled for state-changing actions.
- Never include admin passwords in screenshots, recordings, or documentation.

## Project status

- **GitHub:** [Add repository URL]
- **Live application:** [Add deployment URL, or write “Not deployed”]
- **Demo video:** [Add recording URL]
- **Data status:** [Add actual entry count and number reviewed/verified]

## Acknowledgements

Developed as a submission for the Garuda Prakashan × Rishihood live project selection assignment, Track 3: Dictionary App. AI tools were used during planning, coding assistance, and preparation of draft data; see [`AI_LOG.md`](AI_LOG.md) for disclosure.
