"""
Tests for dictionary models: creation, constraints, ordering and __str__.
"""

from django.db import IntegrityError
from django.test import TestCase

from dictionary.models import DictionaryEntry, Meaning, RomanisedVariant


class DictionaryEntryModelTests(TestCase):
    """Tests for the DictionaryEntry model."""

    def setUp(self):
        self.entry = DictionaryEntry.objects.create(
            headword="पुस्तक",
            transliteration="pustaka",
            pos="noun",
        )

    def test_str_representation(self):
        self.assertEqual(str(self.entry), "पुस्तक (pustaka)")

    def test_headword_is_unique(self):
        """Duplicate headwords must raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            DictionaryEntry.objects.create(
                headword="पुस्तक",
                transliteration="pustaka",
                pos="noun",
            )

    def test_default_is_verified_false(self):
        self.assertFalse(self.entry.is_verified)

    def test_ordering_by_headword(self):
        DictionaryEntry.objects.create(
            headword="आम",
            transliteration="āma",
            pos="noun",
        )
        entries = list(DictionaryEntry.objects.values_list("headword", flat=True))
        self.assertEqual(entries, sorted(entries))

    def test_timestamps_auto_set(self):
        self.assertIsNotNone(self.entry.created_at)
        self.assertIsNotNone(self.entry.updated_at)


class RomanisedVariantModelTests(TestCase):
    """Tests for the RomanisedVariant model."""

    def setUp(self):
        self.entry = DictionaryEntry.objects.create(
            headword="पानी",
            transliteration="pānī",
            pos="noun",
        )

    def test_create_variant(self):
        variant = RomanisedVariant.objects.create(
            entry=self.entry,
            spelling="paani",
        )
        self.assertEqual(str(variant), "paani")
        self.assertEqual(variant.entry, self.entry)

    def test_duplicate_spelling_same_entry_rejected(self):
        """The unique_variant_per_entry constraint must prevent duplicates."""
        RomanisedVariant.objects.create(entry=self.entry, spelling="paani")
        with self.assertRaises(IntegrityError):
            RomanisedVariant.objects.create(entry=self.entry, spelling="paani")

    def test_same_spelling_different_entries_allowed(self):
        """Two different entries may share a spelling variant."""
        other = DictionaryEntry.objects.create(
            headword="पानि",
            transliteration="pāni",
            pos="noun",
        )
        RomanisedVariant.objects.create(entry=self.entry, spelling="paani")
        RomanisedVariant.objects.create(entry=other, spelling="paani")
        self.assertEqual(RomanisedVariant.objects.filter(spelling="paani").count(), 2)

    def test_cascade_delete(self):
        RomanisedVariant.objects.create(entry=self.entry, spelling="paani")
        self.entry.delete()
        self.assertEqual(RomanisedVariant.objects.count(), 0)

    def test_related_name(self):
        RomanisedVariant.objects.create(entry=self.entry, spelling="paani")
        RomanisedVariant.objects.create(entry=self.entry, spelling="pani")
        self.assertEqual(self.entry.romanised_variants.count(), 2)


class MeaningModelTests(TestCase):
    """Tests for the Meaning model."""

    def setUp(self):
        self.entry = DictionaryEntry.objects.create(
            headword="धर्म",
            transliteration="dharma",
            pos="noun",
        )

    def test_create_meaning(self):
        meaning = Meaning.objects.create(
            entry=self.entry,
            text="Duty, righteousness",
            position=1,
        )
        self.assertIn("Duty", str(meaning))

    def test_ordering_by_position(self):
        Meaning.objects.create(entry=self.entry, text="Second sense", position=2)
        Meaning.objects.create(entry=self.entry, text="First sense", position=1)
        meanings = list(self.entry.meaning_items.values_list("position", flat=True))
        self.assertEqual(meanings, [1, 2])

    def test_long_text_truncated_in_str(self):
        long_text = "x" * 100
        meaning = Meaning.objects.create(
            entry=self.entry,
            text=long_text,
            position=1,
        )
        self.assertTrue(str(meaning).endswith("…"))
        self.assertLessEqual(len(str(meaning)), 70)

    def test_cascade_delete(self):
        Meaning.objects.create(entry=self.entry, text="A meaning", position=1)
        self.entry.delete()
        self.assertEqual(Meaning.objects.count(), 0)

    def test_related_name(self):
        Meaning.objects.create(entry=self.entry, text="Sense 1", position=1)
        Meaning.objects.create(entry=self.entry, text="Sense 2", position=2)
        self.assertEqual(self.entry.meaning_items.count(), 2)

