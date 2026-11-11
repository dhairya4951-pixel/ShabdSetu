# ShabdSetu — AI Usage Log

**Project:** ShabdSetu (शब्दसेतु), a bilingual dictionary web application  
**Selection assignment:** Garuda Prakashan × Rishihood — Track 3: Dictionary App  
**Purpose of this log:** Disclose where AI tools assisted and distinguish AI-generated material from decisions, checks, and work performed by the project author.

> **Accuracy note:** This log is written from the development process described by the project author. It does not claim that every generated dictionary record has been independently verified, that every suggested test has passed, or that the author manually wrote all generated code. Update the verification and test-result sections with actual evidence before submission.

## 1. AI tools used

| Tool | How it was used | Work supported |
|---|---|---|
| Google Antigravity | AI-assisted coding and implementation in the project workspace. | Django project development; database models and relationships; Django Admin and the custom management interface; bilingual search implementation; public-facing interface; and iterative development. The project author reports that Antigravity ran a smoke test after each implementation prompt. Exact test commands and outputs should be retained from the project terminal if available. |
| ChatGPT (OpenAI) | Product planning, technical discussion, prompt drafting, dataset drafting, and documentation support. | Helped compare JSON storage with Django models; plan the `DictionaryEntry`, `RomanisedVariant`, and `Meaning` data structure; define the staged Antigravity workflow; specify the search requirements; draft the additional 40 dictionary records (IDs 11–50); and prepare documentation/checklists. |
| Other tools | No other AI tool is recorded here. | Add any additional tool actually used, or remove this row if not applicable. |

## 2. How AI was used during development

AI assistance was used as a development aid rather than as a substitute for checking the finished product. The work was divided into bounded stages so that the application could be implemented and checked incrementally.

1. **Product and architecture planning:** ChatGPT helped turn the assignment brief into a staged implementation plan. The project author chose to use Django models and a custom admin interface rather than keeping the dictionary solely in a JSON file.
2. **Backend implementation:** Antigravity was prompted to implement the Django data models, database relationships, migrations, and admin functionality.
3. **Data import:** Antigravity was prompted to create or adapt an importer for the assignment's JSON data. The intended workflow is to keep the original 10 Garuda records and append the additional 40 records to the existing JSON dataset before importing.
4. **Search implementation:** Antigravity was prompted to build search across Devanagari headwords, IAST transliteration, and common Romanised spellings, with normalization, partial matching, and cautious typo suggestions.
5. **User interface:** Antigravity was prompted to build the public dictionary interface and a separate staff-only custom admin interface while preserving the existing public application.
6. **Dataset drafting:** ChatGPT drafted the additional 40 records (IDs 11–50) in the assignment's requested JSON structure. These records are AI-assisted drafts. Their headwords, IAST forms, grammatical information, meanings, aliases, and example sentences must be checked before they are marked verified.
7. **Documentation:** ChatGPT helped prepare README and AI-log material. The project author must update these documents to match the final repository and actual test results.

## 3. Key prompts and instructions

The development prompts were given to Antigravity in stages rather than as one request to generate the whole application. The main prompt topics were:

- Establish the ShabdSetu product identity, technology constraints, and P0 scope.
- Create Django models for dictionary entries, Romanised variants, and meanings, and configure Django Admin with inline editing.
- Import the original 10 starter records from the assignment. The additional 40 records were intentionally deferred until the application structure was working.
- Implement ranked Devanagari, IAST, and Romanised search, including normalization and careful fuzzy suggestions.
- Build the public homepage, results, word-detail view, no-results state, and responsive layouts.
- Perform a final P0 audit and prepare project documentation.
- Build a custom staff-only dashboard under `/manage/` while retaining Django's built-in `/admin/` interface.
- Import the later 40 records without overwriting or duplicating the original 10.

The prompts were iterative and were refined as project decisions changed. If the reviewer requests the exact prompt text, provide the actual prompt history or conversation links; this log does not reproduce a verbatim transcript.

## 4. AI output, decisions, and corrections

| Area | Decision made by the project author | Reason |
|---|---|---|
| Data storage | Chose Django models and relational records for entries, meanings, and Romanised variants rather than using JSON as the live application data store. JSON remains the import format. | The database supports structured relationships and lets staff maintain dictionary content through the admin interface. |
| Scope | Kept the first release focused on the assignment's P0 requirements. Bookmarks, recent searches, word of the day, and offline support were deferred. | Avoided spending time on optional features before core bilingual search and dictionary accuracy were complete. |
| Dataset timing | Started development with the 10 records supplied in the assignment and prepared the additional 40 separately. | This allowed the application and importer to be developed before expanding the dataset. |
| Search behaviour | Required exact matches to rank above partial/fuzzy suggestions, and fuzzy suggestions to be identified as suggestions rather than certain matches. | Romanised spellings can be ambiguous; a plausible suggestion should not be presented as a guaranteed dictionary match. |
| Admin interface | Added a custom staff-facing management interface while keeping Django Admin available. | The custom interface follows the product's visual identity; the built-in admin remains a useful fallback. |
| Generated dictionary content | Treated the additional 40 entries as drafts requiring human/reference review, not as automatically verified lexicographic content. | AI-generated linguistic data can contain errors in IAST, gender, meanings, and usage. |

Do not add examples of code or suggestions being rejected unless you can identify what was actually rejected or changed in the Antigravity project history.

## 5. Code and application checks

The project author reports that Antigravity ran a smoke test after each implementation prompt. This log does **not** have the terminal output or a test report confirming the exact checks or their results. Record the actual outcomes below before submission.

| Check | Status / evidence to record |
|---|---|
| Smoke test after each Antigravity implementation prompt | Project author reports that these were run. Add the Antigravity output or terminal evidence if available. |
| `python manage.py check` | **Record actual result:** [paste output or write date/result]. |
| `python manage.py test` | **Record actual result:** [number passed/failed and any skipped tests]. |
| Import command run twice to check duplicate handling | **Record actual result:** [entry counts before/after and command output]. |
| Devanagari search | **Record actual queries and results.** |
| Romanised and IAST search | **Record actual queries and results.** |
| Search for a spelling not present in the aliases | **Record the query and whether the correct entry was found.** |
| Partial and fuzzy search | **Record actual examples; distinguish suggestions from exact matches.** |
| Custom admin access control | **Record tests for logged-out, non-staff, and staff accounts.** |
| Create, edit, and delete through custom admin | **Record the actual result.** |
| Mobile layout | **Record screen widths/devices actually checked.** |
| Deployment | **Record the live URL and signed-out check, or state “not deployed”.** |

Do not leave this section with unsupported claims. Remove checks that were not performed and record failures honestly.

## 6. Dictionary data provenance and verification

- **Entries 1–10:** Supplied in the Garuda Prakashan assignment brief.
- **Entries 11–50:** Drafted with ChatGPT assistance for this project. The examples were composed for the application; they should not be represented as quotations from a published dictionary.
- **Reference sources identified for review:**
  - Cologne Digital Sanskrit Dictionaries / Monier-Williams Sanskrit-English Dictionary: https://www.sanskrit-lexicon.uni-koeln.de/ and https://sanskrit-lexicon.github.io/MWS/
  - Sanskrit dictionary interface, University of Hyderabad: https://sanskrit.uohyd.ac.in/SKT/DICO/index.en.html
  - Hindi Shabd-Sindhu, Government of India: https://hindishabdsindhu.rajbhasha.gov.in/
  - Hindi Shabdamitra, CFILT, IIT Bombay: https://www.cfilt.iitb.ac.in/hindishabdamitra/

These are references identified for checking. Listing them here does **not** mean every one of the 50 records has been individually checked against them. Record exactly which entries and fields were checked, and add source details to the corresponding database records only after consulting the source.

Before setting `is_verified=True`, check each record's:

- Devanagari headword and spelling policy.
- IAST transliteration and diacritics.
- Hindi part of speech and grammatical gender, where applicable.
- English glosses and intended sense.
- Romanised aliases, ensuring they are plausible and not misleading collisions.
- Hindi example sentence for spelling, grammar, and natural usage.
- Source name and source URL.

**Current verification status:** [Enter the real count of reviewed/verified entries and the count still awaiting review. Do not assume all 50 are verified.]

## 7. Project author's contribution

The project author made the product and scope decisions, supplied the assignment requirements to the AI tools, selected the Django-based implementation approach, directed the staged development, ran the project locally, and is responsible for the final review, data verification, testing, repository, and submission. AI-generated code and content were treated as material to be integrated and checked, not as proof that the application or data is correct.

Add specific examples of bugs investigated, UI changes made, or technical decisions personally implemented if you can substantiate them from your work.

## 8. Known limitations to disclose

Update this list to reflect the final application:

- Romanised spelling is not standardized across all users; not every possible spelling can be mapped unambiguously to one headword.
- IAST transliteration and informal Roman spellings are different conventions and should not be treated as interchangeable.
- Fuzzy matches can produce false positives, especially for short queries; suggestions should remain visibly distinct from exact matches.
- The initial dataset contains only 50 entries, so vocabulary coverage is limited.
- Entries drafted with AI assistance require individual linguistic and source verification before being described as verified.
- Offline use, user accounts, bookmarks, and recent searches are outside the initial P0 scope unless they were subsequently implemented.

---

**Submission reminder:** Replace the bracketed result fields, remove any statements that do not match the finished project, and keep this log consistent with the actual code, dataset, test output, and demo.
