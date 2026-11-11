"""
Tests for dictionary admin configuration.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from dictionary.admin import DictionaryEntryAdmin
from dictionary.models import DictionaryEntry


class DictionaryEntryAdminTests(TestCase):
    """Verify that the admin is properly configured."""

    def setUp(self):
        self.admin = DictionaryEntryAdmin(DictionaryEntry, AdminSite())

    def test_list_display_fields(self):
        expected = ["headword", "transliteration", "pos", "is_verified", "updated_at"]
        self.assertEqual(self.admin.list_display, expected)

    def test_search_fields(self):
        self.assertIn("headword", self.admin.search_fields)
        self.assertIn("transliteration", self.admin.search_fields)
        self.assertIn("romanised_variants__spelling", self.admin.search_fields)
        self.assertIn("meaning_items__text", self.admin.search_fields)

    def test_list_filters(self):
        self.assertIn("pos", self.admin.list_filter)
        self.assertIn("is_verified", self.admin.list_filter)

    def test_readonly_timestamps(self):
        self.assertIn("created_at", self.admin.readonly_fields)
        self.assertIn("updated_at", self.admin.readonly_fields)

    def test_inlines_registered(self):
        inline_models = [inline.model for inline in self.admin.inlines]
        from dictionary.models import Meaning, RomanisedVariant
        self.assertIn(RomanisedVariant, inline_models)
        self.assertIn(Meaning, inline_models)

