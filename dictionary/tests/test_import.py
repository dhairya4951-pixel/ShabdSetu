"""
Tests for the import_dictionary management command.
"""

import json
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from dictionary.models import DictionaryEntry, Meaning, RomanisedVariant


class ImportDictionaryCommandTests(TestCase):
    """Tests for `python manage.py import_dictionary`."""

    def test_import_creates_entries(self):
        """Importing the default data file creates all 10 starter entries."""
        call_command("import_dictionary", verbosity=0)

        self.assertEqual(DictionaryEntry.objects.count(), 10)

    def test_import_creates_meanings(self):
        """Every entry should have at least one meaning."""
        call_command("import_dictionary", verbosity=0)

        for entry in DictionaryEntry.objects.all():
            self.assertGreater(
                entry.meaning_items.count(),
                0,
                f"{entry.headword} has no meanings",
            )

    def test_import_creates_variants(self):
        """Every entry should have at least one romanised variant."""
        call_command("import_dictionary", verbosity=0)

        for entry in DictionaryEntry.objects.all():
            self.assertGreater(
                entry.romanised_variants.count(),
                0,
                f"{entry.headword} has no romanised variants",
            )

    def test_meaning_order_preserved(self):
        """Meanings should be ordered by position, matching the JSON array order."""
        call_command("import_dictionary", verbosity=0)

        # Pick an entry with multiple meanings.
        multi = (
            DictionaryEntry.objects
            .filter(meaning_items__position__gt=1)
            .distinct()
            .first()
        )
        if multi:
            positions = list(
                multi.meaning_items.values_list("position", flat=True)
            )
            self.assertEqual(positions, sorted(positions))

    def test_idempotent_no_duplicates(self):
        """Running the import twice must not create duplicate entries."""
        call_command("import_dictionary", verbosity=0)
        call_command("import_dictionary", verbosity=0)

        self.assertEqual(DictionaryEntry.objects.count(), 10)

    def test_variants_not_duplicated_on_reimport(self):
        """Running the import twice must not duplicate romanised variants."""
        call_command("import_dictionary", verbosity=0)
        count_before = RomanisedVariant.objects.count()

        call_command("import_dictionary", verbosity=0)
        count_after = RomanisedVariant.objects.count()

        self.assertEqual(count_before, count_after)

    def test_is_verified_defaults_to_false(self):
        """Imported entries must not be auto-verified."""
        call_command("import_dictionary", verbosity=0)

        verified = DictionaryEntry.objects.filter(is_verified=True).count()
        self.assertEqual(verified, 0)

    def test_update_existing_flag(self):
        """With --update-existing, entries should be updated, not skipped."""
        call_command("import_dictionary", verbosity=0)

        # Manually change an entry.
        entry = DictionaryEntry.objects.first()
        entry.transliteration = "MODIFIED"
        entry.save()

        # Re-import with update flag.
        call_command("import_dictionary", "--update-existing", verbosity=0)

        entry.refresh_from_db()
        self.assertNotEqual(entry.transliteration, "MODIFIED")

    def test_update_preserves_verified_flag(self):
        """--update-existing must not reset is_verified."""
        call_command("import_dictionary", verbosity=0)

        entry = DictionaryEntry.objects.first()
        entry.is_verified = True
        entry.save()

        call_command("import_dictionary", "--update-existing", verbosity=0)

        entry.refresh_from_db()
        self.assertTrue(entry.is_verified)

    def test_invalid_json_raises_error(self):
        """A malformed JSON file should raise CommandError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{not valid json")
            f.flush()

            with self.assertRaises(CommandError):
                call_command("import_dictionary", "--file", f.name, verbosity=0)

    def test_missing_fields_raises_error(self):
        """An entry missing required fields should raise CommandError."""
        bad_data = [{"headword": "test"}]  # missing transliteration, pos, meanings
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(bad_data, f)
            f.flush()

            with self.assertRaises(CommandError):
                call_command("import_dictionary", "--file", f.name, verbosity=0)

    def test_invalid_pos_raises_error(self):
        """An entry with an unrecognised POS value should raise CommandError."""
        bad_data = [
            {
                "id": 99,
                "headword": "परीक्षा",
                "transliteration": "parīkṣā",
                "pos": "INVALID",
                "meanings": ["Test"],
            }
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(bad_data, f)
            f.flush()

            with self.assertRaises(CommandError):
                call_command("import_dictionary", "--file", f.name, verbosity=0)

    def test_pos_normalisation(self):
        """POS strings like 'noun (f.)' should be normalised to 'noun'."""
        call_command("import_dictionary", verbosity=0)

        # शिक्षा has POS "noun (f.)" in the JSON, should become "noun".
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        self.assertEqual(entry.pos, "noun")

    def test_specific_entry_shiksha(self):
        """Spot-check शिक्षा entry from the Garuda dataset."""
        call_command("import_dictionary", verbosity=0)

        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        self.assertEqual(entry.transliteration, "śikṣā")
        self.assertEqual(entry.pos, "noun")
        self.assertEqual(entry.example, "शिक्षा हर बच्चे का अधिकार है।")

        meanings = list(entry.meaning_items.order_by("position").values_list("text", flat=True))
        self.assertEqual(meanings, ["education", "learning"])

        variants = set(entry.romanised_variants.values_list("spelling", flat=True))
        self.assertEqual(variants, {"shiksha", "siksha", "shiksa"})

    def test_specific_entry_satya(self):
        """Spot-check सत्य entry from the Garuda dataset."""
        call_command("import_dictionary", verbosity=0)

        entry = DictionaryEntry.objects.get(headword="सत्य")
        self.assertEqual(entry.transliteration, "satya")
        self.assertEqual(entry.pos, "noun")

        meanings = list(entry.meaning_items.values_list("text", flat=True))
        self.assertEqual(meanings, ["truth"])

        variants = set(entry.romanised_variants.values_list("spelling", flat=True))
        self.assertEqual(variants, {"satya", "saty"})
