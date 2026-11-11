# ShabdSetu — Data Review

## Summary

| Metric                          | Count |
|---------------------------------|-------|
| Total entries                   | 10    |
| Original Garuda starter entries | 10    |
| Additional entries              | 0     |
| Remaining entries required      | 40    |

## Verification Status

| # | Headword  | Transliteration | POS (source) | Meanings | Variants | Verified |
|---|-----------|-----------------|--------------|----------|----------|----------|
| 1 | शिक्षा   | śikṣā           | noun (f.)    | 2        | 3        | ❌       |
| 2 | भाषा     | bhāṣā           | noun (f.)    | 2        | 3        | ❌       |
| 3 | शब्द     | śabda           | noun (m.)    | 2        | 3        | ❌       |
| 4 | प्रकाश   | prakāśa         | noun (m.)    | 2        | 3        | ❌       |
| 5 | वृक्ष    | vṛkṣa           | noun (m.)    | 1        | 3        | ❌       |
| 6 | समय      | samaya          | noun (m.)    | 2        | 3        | ❌       |
| 7 | कर्म     | karma           | noun (m.)    | 2        | 2        | ❌       |
| 8 | शांति    | śānti           | noun (f.)    | 2        | 3        | ❌       |
| 9 | प्रेम    | prema           | noun (m.)    | 2        | 2        | ❌       |
|10 | सत्य     | satya           | noun (m.)    | 1        | 2        | ❌       |

**None of the entries are marked as verified.**
Verification requires independent review by a human editor through Django Admin.
The import command never auto-sets `is_verified = True`.

## POS Distribution

All 10 entries are nouns.

| POS in source data | Count | Stored as |
|--------------------|-------|-----------|
| noun (m.)          | 6     | noun      |
| noun (f.)          | 4     | noun      |

> **Note:** The Garuda dataset includes grammatical gender in the POS field
> (`noun (m.)`, `noun (f.)`). The import command normalises these to `noun`
> for the model's POS field. The original gender information is preserved
> in `entries.json` and can be used if a gender field is added later.

## Data Source

These 10 entries are the original starter set from the
Garuda Prakashan × Rishihood dictionary project assignment.

## Next Steps

- [ ] Prepare and verify the remaining 40 entries.
- [ ] Review all 10 starter entries through Django Admin.
- [ ] Mark entries as verified only after human review.
- [ ] Consider adding a `gender` field to the model for Hindi noun genders.
- [ ] Ensure at least 50 total entries before final submission.
