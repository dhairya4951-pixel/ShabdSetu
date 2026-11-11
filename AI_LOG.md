# ShabdSetu — AI Usage Log

**Project:** ShabdSetu (शब्दसेतु)  
**Assignment:** Garuda Prakashan × Rishihood — Track 3: Dictionary App  
**Purpose:** Disclose how AI tools assisted with planning, implementation, dataset preparation, debugging support, and documentation, while distinguishing generated material from decisions and checks performed by the project author.

## 1. Summary of AI use

AI tools were used throughout development as assistants for planning, coding, data drafting, debugging, and documentation. The project was developed iteratively: requirements were divided into stages, Antigravity was given bounded implementation prompts, and the resulting application was run and tested during development.

The project author retained responsibility for choosing the project direction, deciding the technical approach, directing the implementation, running the application and commands, reviewing the outputs, and preparing the final submission.

AI use is disclosed in accordance with the assignment instructions. AI-generated code and dictionary content were not treated as automatically correct.

## 2. AI tools used

| Tool | Use in this project |
|---|---|
| **Google Antigravity** | AI-assisted implementation in the project workspace. It was prompted in stages to build the Django foundation, relational models, Django Admin configuration, JSON importer, bilingual search functionality, public dictionary interface, custom staff management interface, tests, and project documentation. |
| **ChatGPT (OpenAI)** | Product and architecture discussion, comparison of JSON storage with Django models, preparation of staged Antigravity prompts, search-design discussion, drafting of the additional 40 dictionary records (IDs 11–50), debugging guidance based on terminal output, and preparation of README and submission documentation. |

No other AI tool is recorded here. Add one only if it was actually used.

## 3. What AI assisted with

### 3.1 Product planning and architecture

ChatGPT helped translate the assignment brief into a staged development plan and discuss the trade-offs between keeping the dictionary in a JSON file and using Django models.

The project author selected a Django ORM-based relational design with three models:

- `DictionaryEntry` for the main headword and entry fields.
- `RomanisedVariant` for multiple Roman spellings related to an entry.
- `Meaning` for multiple meanings related to an entry.

JSON was retained as the dataset/import format; the database is used by the running application.

### 3.2 Backend and content management

Antigravity was prompted to implement the Django project foundation, models, relationships, migrations, Django Admin configuration, and a custom staff-facing management interface at `/manage/`.

The custom management interface was intended to let authorized staff create, edit, review, and delete dictionary entries while retaining Django's built-in `/admin/` interface.

### 3.3 Bilingual search

Antigravity was prompted to build a separate search implementation that can consider Devanagari headwords, IAST transliteration, stored Romanised variants, normalization, partial matches, and typo-tolerant suggestions.

The intended ranking principle is that exact matches should be preferred over weaker matches, and fuzzy candidates should be displayed as suggestions rather than guaranteed answers.

### 3.4 Dataset drafting

The original 10 entries were supplied by the Garuda assignment brief.

ChatGPT assisted in drafting 40 additional records (IDs 11–50) in the assignment's JSON structure. These drafts include Devanagari headwords, IAST forms, Romanised variants, parts of speech, English meanings, and Hindi example sentences.

The additional records are AI-assisted drafts. They require human/reference review for spelling, transliteration, grammatical information, meanings, aliases, example sentences, and source attribution. Their presence in the database does not mean that they are linguistically verified.

### 3.5 Frontend and documentation

Antigravity was prompted to implement the public dictionary pages and responsive design using Django templates, HTML, CSS, and JavaScript, and later to add a separate custom staff management interface.

ChatGPT assisted with README structure, AI-use disclosure, and submission checklists. The final documentation should remain consistent with the actual code and repository.

## 4. Important prompt themes

Development prompts were provided to Antigravity in bounded stages rather than asking it to generate the entire application in one request. The main prompt themes were:

1. Define the ShabdSetu product objective, technology stack, coding conventions, and P0 scope.
2. Create the Django models and relationships for entries, spelling variants, and meanings.
3. Configure Django Admin with inline management of variants and meanings.
4. Import the 10 starter records from the assignment and later extend the existing JSON dataset to 50 records.
5. Implement Devanagari, IAST, and Romanised search with normalization, partial matching, and cautious fuzzy suggestions.
6. Build the public homepage, search results, entry detail page, no-results state, and responsive layout.
7. Add a custom, staff-restricted management interface at `/manage/`.
8. Run and fix tests, then prepare project documentation.

This section summarizes the prompt themes; it is not a verbatim transcript of every prompt. The actual Antigravity prompt history can be provided separately if requested.

## 5. Human decisions and review

The project author directed the development process and made the following product and technical decisions:

- Chose Django and a server-rendered frontend rather than adding a separate frontend framework.
- Chose relational database models so that multiple meanings and spelling variants could be managed as related records.
- Kept JSON as an import format rather than the live application's only data store.
- Deferred optional features such as bookmarks, recent searches, word of the day, and offline support until the core assignment requirements were implemented.
- Kept exact matches distinct from partial and fuzzy suggestions to reduce the risk of presenting an uncertain spelling match as authoritative.
- Requested a custom staff management interface while retaining Django Admin.
- Reviewed terminal output and used the reported importer error to direct a correction to the unsupported part-of-speech label for `आकाश`.

The project author ran the reported database-count and test commands and shared their output during development. This log does not claim that the author manually wrote every line of AI-assisted code.

## 6. Debugging and corrections

During dataset import, the importer rejected entry `आकाश` because its part-of-speech value was `noun (m./n.)`, while the importer's accepted vocabulary included `noun`, `noun (f.)`, `noun (m.)`, and `noun (n.)`, but not the combined label.

The dataset value was corrected to an accepted label (`noun (m.)`) and the import/test process was run again. The final test output shared during development completed successfully.

This illustrates an important check in the workflow: generated dataset values must conform to the application's actual validation rules. The importer validation was not intentionally weakened to bypass the error.

## 7. Test and database evidence

The following results were shared from the development environment.

### Automated tests

The final test output shared during development reported:

```text
Ran 134 tests in 18.980s

OK
```

**Reported result:** 134 tests passed; no test failures or errors were reported in that final run.

The test output included repeated dataset-import setup and tests covering search normalization, partial matching, fuzzy suggestion labels, homepage behaviour, search results, detail pages, and user navigation. This is evidence of the automated test suite at that point in development. It is not proof that every possible browser, device, production, or linguistic scenario has been tested.

### Database counts

The project author ran a Django shell query and shared these counts:

| Model | Reported count |
|---|---:|
| `DictionaryEntry` | 50 |
| `RomanisedVariant` | 129 |
| `Meaning` | 131 |

These are the latest actual development-database counts shared during the conversation.

### Verification status

An earlier database query reported:

- Verified entries: 1
- Unverified entries: 49

This was the last verification-status count shared. Recheck the current database if any entries have since been reviewed or their status changed. Do not mark entries verified merely to improve the reported number.

### Checks not claimed by this log

The evidence shared does not establish that:

- All 50 records have been individually verified by a language expert.
- Every possible Romanised spelling or transliteration scheme is supported.
- The application has been deployed to a production environment.
- Every manual mobile/browser/accessibility check has been completed.
- Importer idempotency has been proven by a separate repeated-import count comparison on the normal development database.

Only add claims in these areas after performing and recording the relevant checks.

## 8. Dataset provenance and linguistic review

- **IDs 1–10:** Starter records supplied in the Garuda Prakashan assignment.
- **IDs 11–50:** Drafted with ChatGPT assistance for this project.
- **Example sentences for IDs 11–50:** Composed as application examples; they are not presented as quotations from a published dictionary.

Reference resources identified as useful for review include:

- Cologne Digital Sanskrit Dictionaries: https://www.sanskrit-lexicon.uni-koeln.de/
- Monier-Williams digital corpus: https://sanskrit-lexicon.github.io/MWS/
- Hindi Shabd-Sindhu: https://hindishabdsindhu.rajbhasha.gov.in/
- Hindi Shabdamitra, CFILT, IIT Bombay: https://www.cfilt.iitb.ac.in/hindishabdamitra/

These are reference resources identified for review; listing them does not mean that each entry was checked against them. Record a source name and URL for an entry only after actually consulting that source. Follow its licence and attribution requirements if published content is copied or adapted.

Before marking an entry as verified, review:

1. Devanagari spelling.
2. IAST transliteration and diacritics.
3. Part of speech and grammatical gender under the chosen language convention.
4. Intended sense and English meanings.
5. Romanised variants and possible ambiguities.
6. Hindi example sentence grammar, spelling, and naturalness.
7. Source attribution and licence requirements.

## 9. Known limitations

- Romanised spelling is not standardized; users may enter regional or personal variants not present in the dataset.
- IAST transliteration and informal Roman spellings are different conventions.
- Fuzzy matching can produce false positives, particularly for short or ambiguous queries.
- The dataset contains 50 records and is a focused prototype, not comprehensive Hindi or Sanskrit coverage.
- The additional 40 records require individual linguistic/source review before being described as verified.
- The initial P0 release does not include offline support, bookmarks, recent searches, or word-of-the-day functionality.

## 10. Deployment and submission status

Deployment was not completed as part of the work described in this log. The assignment describes a deployed link or APK as optional (“if possible”), and the project was kept focused on the working Django application, dataset, automated tests, and submission documentation.

The source repository and demonstration recording should be supplied through the submission materials. Do not describe a local development server as a public deployment.

## 11. Closing disclosure

AI tools materially assisted with planning, code implementation, search design, draft dictionary content, debugging guidance, and documentation. The project author directed the work, made product and architecture decisions, ran the reported commands, reviewed the outputs, and remains responsible for the correctness of the submitted application and dictionary data.

The additional 40 dictionary entries are disclosed as AI-assisted drafts and are not represented as individually verified scholarly definitions. The reported automated test result is included above without claiming broader checks that were not evidenced.
