# ShabdSetu (शब्दसेतु)

**A bilingual dictionary that helps people find Indian-language words using Devanagari, IAST, and familiar Romanised spellings.**

ShabdSetu is a Django-based dictionary web application developed for the **Garuda Prakashan × Rishihood — Track 3: Dictionary App** selection assignment.

The project addresses a practical access problem: users may know how an Indian-language word sounds but prefer typing with a standard Roman/English keyboard. ShabdSetu lets users search using Devanagari, IAST transliteration, and common Romanised spellings, then view the corresponding dictionary entry.

## Project status

- **Application:** Implemented as a Django web application.
- **Dictionary dataset:** 50 entries in the local database.
- **Related records:** 129 Romanised variants and 131 meaning records in the latest database count shared during development.
- **Automated tests:** The reported final Django test run completed **134 tests successfully** (`OK`).
- **Deployment:** Not deployed. The assignment describes a deployed link or APK as optional (“if possible”); the project is being submitted with its source repository and demonstration materials instead.
- **Data verification:** The additional 40 records (IDs 11–50) were drafted with AI assistance and should not be represented as fully linguistically verified. The latest verification count shared during development was 1 verified and 49 unverified; check the live database before making a more current claim.

## Features

### Dictionary experience

- Search using Devanagari headwords.
- Search using IAST transliteration.
- Search using stored common Romanised spelling variants.
- Normalize supported input differences such as case, diacritics, and spelling forms where implemented.
- Support partial matching and typo-tolerant suggestions.
- Distinguish fuzzy suggestions from exact matches.
- Display entry details: headword, IAST transliteration, Romanised variants, part of speech, meanings, and example sentence.
- Show a clear no-results state.
- Provide a responsive interface for desktop and mobile screens.

### Content management

- Django ORM models for dictionary entries, Romanised variants, and meanings.
- Django's built-in Admin interface for staff maintenance.
- A custom staff-facing management interface at `/manage/`.
- Entry source and verification metadata where supported by the model.
- Related meanings and Romanised variants managed as separate database records.

Access to `/manage/` and `/admin/` is intended for authorized staff accounts.

## Technology

- Python
- Django
- SQLite for local development
- Django ORM and Django Admin
- Django Templates
- HTML, CSS, and vanilla JavaScript

The exact installed package versions are recorded in `requirements.txt`. The search implementation and dependencies should be checked in `dictionary/search.py` and `requirements.txt`; this README does not assume a particular transliteration or fuzzy-matching package unless it is actually present.

## Project structure

The project contains a Django project configuration package and a `dictionary` application. The important application files include:

```text
ShabdSetu/
├── manage.py
├── requirements.txt
├── README.md
├── AI_LOG.md
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
└── Django project configuration package
```

The repository also contains the project's static assets, tests, and configuration files. The Django configuration package name is intentionally described generically here; use the actual package name visible in the repository when navigating the source.

## Getting started locally

### 1. Clone the repository

Open the public repository on GitHub, select **Code → HTTPS**, and copy the clone command shown there. Paste that command into your terminal. Then change into the repository directory created by Git:

```bash
cd ShabdSetu
```

If your repository has a different name, use the directory name created by the clone command.

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure local settings

Use the settings and environment-variable conventions already present in the repository. If the project uses a `.env` file, create it locally and do not commit it. Keep secret keys and credentials out of Git.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Import the dictionary dataset

The combined dataset is maintained in:

```text
dictionary/data/entries.json
```

It contains the 10 starter records supplied in the assignment and 40 additional draft records (IDs 11–50).

Run the project's importer:

```bash
python manage.py import_dictionary
```

The importer implementation is the source of truth for its exact duplicate-handling and update behaviour. Review `dictionary/management/commands/import_dictionary.py` before rerunning it against a database containing admin-edited content.

After importing, confirm the database counts:

```bash
python manage.py shell
```

Then:

```python
from dictionary.models import DictionaryEntry, RomanisedVariant, Meaning

print("Entries:", DictionaryEntry.objects.count())
print("Variants:", RomanisedVariant.objects.count())
print("Meanings:", Meaning.objects.count())
```

The latest counts shared during development were:

- Dictionary entries: 50
- Romanised variants: 129
- Meaning records: 131

### 7. Create a staff account

```bash
python manage.py createsuperuser
```

Use a strong password. Do not include credentials in the repository, documentation, or screen recording.

### 8. Run the development server

```bash
python manage.py runserver
```

Open the local address printed by Django, normally `http://127.0.0.1:8000/`.

- Public dictionary: `/`
- Custom management interface: `/manage/`
- Django Admin: `/admin/`

The management and admin routes are intended for authorized staff users.

## How search works

ShabdSetu's search implementation is designed to consider multiple ways a user may enter the same word:

1. Devanagari headword.
2. Stored Romanised spelling variants.
3. IAST transliteration.
4. Normalized forms, including supported case and diacritic differences.
5. Partial/prefix matches.
6. Fuzzy candidates for likely spelling errors.

Exact matches should be ranked above weaker matches. A fuzzy result is a suggestion, not a guarantee that the user intended that word. Informal Romanised spellings are not standardized, so not every spelling can be resolved unambiguously.

The automated test suite includes cases for normalized forms, partial matching, fuzzy suggestion labels, exact Devanagari and Romanised searches, result labels, and the homepage-to-detail journey. See `dictionary/search.py` and the tests for the exact implemented behaviour.

## Data model

The dictionary uses three related Django models:

- **`DictionaryEntry`** — stores the Devanagari headword, IAST transliteration, part of speech, example sentence, and supported source/verification metadata.
- **`RomanisedVariant`** — stores an alternative Roman spelling linked to a dictionary entry.
- **`Meaning`** — stores an individual meaning linked to a dictionary entry, with a position field to preserve display order.

This relational structure supports multiple spellings and meanings for a single headword and allows staff to maintain content through the management interfaces.

## Testing

Run the Django checks and tests locally:

```bash
python manage.py check
python manage.py test
```

The final test output shared during development reported:

```text
Ran 134 tests in 18.980s

OK
```

This is the reported automated test result, not a claim that every possible manual, browser, device, production, or linguistic scenario has been tested.

Recommended manual checks before review:

- Devanagari search, such as `शिक्षा` and `धर्म`.
- Romanised search, such as `shiksha`, `dharma`, and `prakriti`.
- IAST search, such as `śikṣā`.
- Case and spacing variations.
- A spelling not explicitly present as an alias.
- Partial queries and typo suggestions.
- A query with no match.
- Entry details and displayed Devanagari text.
- Staff-only access to `/manage/` and `/admin/`.
- Create, edit, and delete flows in the management interface.
- Narrow mobile and desktop layouts.

## Data quality, provenance, and AI disclosure

The first 10 records were supplied in the Garuda Prakashan assignment brief. The additional 40 records (IDs 11–50) were drafted with ChatGPT assistance for this project. Their example sentences were composed for the application and are not presented as quotations from a published dictionary.

The additional entries require human/reference review for Devanagari spelling, IAST transliteration, grammatical information, English glosses, aliases, example sentences, and source attribution.

Reference resources identified for review include:

- [Cologne Digital Sanskrit Dictionaries](https://www.sanskrit-lexicon.uni-koeln.de/)
- [Monier-Williams digital corpus](https://sanskrit-lexicon.github.io/MWS/)
- [Hindi Shabd-Sindhu](https://hindishabdsindhu.rajbhasha.gov.in/)
- [Hindi Shabdamitra — CFILT, IIT Bombay](https://www.cfilt.iitb.ac.in/hindishabdamitra/)

Listing a reference does not mean that every entry has been checked against it. Record a source name and URL for an entry only after actually consulting that source. Follow the source's licence and attribution requirements before copying or adapting published definitions.

AI use is disclosed in [`AI_LOG.md`](AI_LOG.md). AI-generated content has not been treated as automatically authoritative.

## Trade-offs and known limitations

- The application prioritizes a focused dictionary lookup experience over user accounts and social features.
- Romanised spellings vary by region and individual habit; coverage is necessarily incomplete.
- IAST and informal Romanised spellings are different conventions and should not be treated as interchangeable.
- Fuzzy matching can produce false positives, especially for short queries.
- A 50-entry dataset is a small prototype, not comprehensive Hindi or Sanskrit coverage.
- The additional 40 entries require individual linguistic and source review before being marked verified.
- Offline support, bookmarks, recent searches, and word-of-the-day functionality are outside the initial P0 scope.

## What could be built with two more weeks

1. Establish a documented transliteration policy and build a benchmark of real Romanised queries.
2. Expand the dictionary through a reviewed editorial workflow with per-entry provenance.
3. Improve ranking and measure false positives for ambiguous and short queries.
4. Add user bookmarks and recent searches with appropriate privacy controls.
5. Improve accessibility and test with people who routinely type Indian-language words using Roman letters.
6. Evaluate offline/PWA support after defining safe caching and data-update behaviour.

## Security notes

- Keep `SECRET_KEY`, database credentials, and deployment tokens out of Git.
- Do not commit `.env` files.
- Restrict `/manage/` and `/admin/` to authorized staff.
- Keep CSRF protection enabled for state-changing actions.
- Use secure production settings if the application is deployed.

## Project and submission links

The application was not deployed as part of this submission preparation; the assignment describes deployment as optional (“if possible”). The source repository and required demonstration materials should be linked directly in the Google Form and submission folder.

## Acknowledgements

Developed for the **Garuda Prakashan × Rishihood — Track 3: Dictionary App** selection assignment.

AI tools were used for planning, coding assistance, preparation of draft dictionary content, and documentation. See [`AI_LOG.md`](AI_LOG.md) for a detailed disclosure.
