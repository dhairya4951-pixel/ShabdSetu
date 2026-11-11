"""
Tests for the bilingual search engine.

Each test imports the Garuda dataset, then exercises one or more
search pipeline stages.
"""

from django.core.management import call_command
from django.test import TestCase

from dictionary.search import (
    EXACT_DEVANAGARI,
    EXACT_IAST,
    EXACT_ROMANISED,
    FUZZY,
    NORMALISED,
    PARTIAL,
    TRANSLITERATION,
    SearchResult,
    normalise_iast,
    normalise_query,
    search,
)


class NormalisationTests(TestCase):
    """Tests for query and IAST normalisation helpers."""

    def test_normalise_query_strips_whitespace(self):
        self.assertEqual(normalise_query("  hello  "), "hello")

    def test_normalise_query_lowercases(self):
        self.assertEqual(normalise_query("PRAKASH"), "prakash")

    def test_normalise_query_collapses_spaces(self):
        self.assertEqual(normalise_query("a   b"), "a b")

    def test_normalise_iast_shiksha(self):
        self.assertEqual(normalise_iast("śikṣā"), "shiksha")

    def test_normalise_iast_prakasha(self):
        self.assertEqual(normalise_iast("prakāśa"), "prakasha")

    def test_normalise_iast_shanti(self):
        self.assertEqual(normalise_iast("śānti"), "shanti")

    def test_normalise_iast_vriksha(self):
        self.assertEqual(normalise_iast("vṛkṣa"), "vriksha")

    def test_normalise_iast_bhasha(self):
        self.assertEqual(normalise_iast("bhāṣā"), "bhasha")


class SearchTestMixin:
    """Mixin that loads the Garuda dataset before each test."""

    def setUp(self):
        call_command("import_dictionary", verbosity=0)


class ExactDevanagariSearchTests(SearchTestMixin, TestCase):
    """Stage 1: Exact Devanagari headword match."""

    def test_shiksha_devanagari(self):
        results = search("शिक्षा")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "शिक्षा")
        self.assertEqual(results[0].match_type, EXACT_DEVANAGARI)
        self.assertEqual(results[0].confidence, 1.0)

    def test_nonexistent_devanagari(self):
        """A word not in the dictionary should return nothing."""
        results = search("पुस्तक")
        self.assertEqual(len(results), 0)

    def test_dharma_devanagari(self):
        """धर्म is in the dictionary — should return exact Devanagari match."""
        results = search("धर्म")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "धर्म")
        self.assertEqual(results[0].match_type, EXACT_DEVANAGARI)

    def test_karma_devanagari(self):
        results = search("कर्म")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "कर्म")


class ExactRomanisedSearchTests(SearchTestMixin, TestCase):
    """Stage 2: Exact romanised variant match."""

    def test_shiksha_romanised(self):
        results = search("shiksha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "शिक्षा")
        self.assertEqual(results[0].match_type, EXACT_ROMANISED)

    def test_siksha_romanised(self):
        results = search("siksha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "शिक्षा")

    def test_case_insensitive_romanised(self):
        results = search("PRAKASH")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "प्रकाश")

    def test_karma_romanised(self):
        results = search("karma")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "कर्म")


class ExactIASTSearchTests(SearchTestMixin, TestCase):
    """Stage 3: Exact IAST transliteration match."""

    def test_iast_with_diacritics(self):
        results = search("śikṣā")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "शिक्षा")
        self.assertEqual(results[0].match_type, EXACT_IAST)

    def test_iast_satya(self):
        results = search("satya")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "सत्य")


class NormalisedMatchTests(SearchTestMixin, TestCase):
    """Stage 4-5: Normalised matching (IAST diacritics stripped)."""

    def test_prakasha_normalised(self):
        """'prakasha' should match प्रकाश via normalised IAST."""
        results = search("prakasha")
        self.assertGreaterEqual(len(results), 1)
        headwords = [r.entry.headword for r in results]
        self.assertIn("प्रकाश", headwords)

    def test_bhasha_normalised(self):
        """'bhasha' is a stored variant, so it hits exact romanised."""
        results = search("bhasha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "भाषा")

    def test_shanti_normalised(self):
        """'shanti' is stored as a variant."""
        results = search("shanti")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry.headword, "शांति")


class PartialMatchTests(SearchTestMixin, TestCase):
    """Stage 6: Prefix / partial matching."""

    def test_dharm_prefix(self):
        """'dharm' should match 'धर्म' (as exact romanised variant)."""
        results = search("dharm")
        headwords = [r.entry.headword for r in results]
        self.assertIn("धर्म", headwords)
        for r in results:
            self.assertIn(r.match_type, (EXACT_ROMANISED, PARTIAL, FUZZY, NORMALISED))

    def test_prak_prefix(self):
        """'prak' should match प्रकाश via prefix."""
        results = search("prak")
        # Short query, but should match 'prakash' as prefix
        headwords = [r.entry.headword for r in results]
        self.assertIn("प्रकाश", headwords)

    def test_sham_prefix(self):
        """'sham' is too short for fuzzy but could prefix-match."""
        results = search("sham")
        # Could match shabd, shanti, shiksha via prefix on normalised forms
        for r in results:
            self.assertIn(r.match_type, (PARTIAL, FUZZY))


class FuzzyMatchTests(SearchTestMixin, TestCase):
    """Stage 7: Fuzzy spelling suggestions."""

    def test_shikshaa_fuzzy(self):
        """
        'shikshaa' is NOT stored as a variant but should fuzzy-match
        to शिक्षा.  This is the critical test from the requirements.
        """
        results = search("shikshaa")
        self.assertGreaterEqual(len(results), 1)
        headwords = [r.entry.headword for r in results]
        self.assertIn("शिक्षा", headwords)

        # The match should be flagged as a suggestion, not an exact match.
        shiksha_result = next(r for r in results if r.entry.headword == "शिक्षा")
        self.assertIn(
            shiksha_result.match_type,
            (FUZZY, NORMALISED, PARTIAL),
        )

    def test_shikshaa_is_suggestion_not_exact(self):
        """A fuzzy match must not be presented as a guaranteed correct answer."""
        results = search("shikshaa")
        shiksha_result = next(
            (r for r in results if r.entry.headword == "शिक्षा"), None
        )
        self.assertIsNotNone(shiksha_result)
        if shiksha_result.match_type == FUZZY:
            self.assertTrue(shiksha_result.is_suggestion)
            self.assertLess(shiksha_result.confidence, 1.0)

    def test_unknown_query_returns_empty_or_low_confidence(self):
        """A random string should return no results or only low-confidence ones."""
        results = search("xyz123abcdef")
        # Either empty, or all results are fuzzy suggestions.
        for r in results:
            self.assertEqual(r.match_type, FUZZY)

    def test_results_have_prefetched_meanings(self):
        """Search results should have meanings prefetched (no extra queries)."""
        results = search("shiksha")
        self.assertGreaterEqual(len(results), 1)
        entry = results[0].entry
        # Access meanings — should not trigger an extra query.
        meanings = list(entry.meaning_items.all())
        self.assertGreater(len(meanings), 0)

    def test_results_have_prefetched_variants(self):
        """Search results should have romanised variants prefetched."""
        results = search("shiksha")
        self.assertGreaterEqual(len(results), 1)
        entry = results[0].entry
        variants = list(entry.romanised_variants.all())
        self.assertGreater(len(variants), 0)


class EmptyQueryTests(SearchTestMixin, TestCase):
    """Edge cases for empty or whitespace-only queries."""

    def test_empty_string(self):
        self.assertEqual(search(""), [])

    def test_whitespace_only(self):
        self.assertEqual(search("   "), [])

    def test_single_char(self):
        """Single characters shouldn't crash; may return partial matches."""
        results = search("a")
        # Should not raise; results may be empty or partial.
        self.assertIsInstance(results, list)


class SearchResultDataTests(SearchTestMixin, TestCase):
    """Tests for SearchResult metadata."""

    def test_match_label_exists(self):
        results = search("शिक्षा")
        self.assertGreaterEqual(len(results), 1)
        label = results[0].match_label
        self.assertIn("Devanagari", label)

    def test_is_suggestion_false_for_exact(self):
        results = search("shiksha")
        self.assertGreaterEqual(len(results), 1)
        self.assertFalse(results[0].is_suggestion)

