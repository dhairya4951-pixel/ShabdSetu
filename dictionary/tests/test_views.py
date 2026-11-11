"""
Tests for dictionary views and the full user journey.
"""

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from dictionary.models import DictionaryEntry


class ViewTestMixin:
    """Mixin that loads the Garuda dataset before each test."""

    def setUp(self):
        call_command("import_dictionary", verbosity=0)
        self.client = Client()


class HomepageTests(ViewTestMixin, TestCase):
    """Tests for the homepage at /."""

    def test_homepage_loads(self):
        response = self.client.get(reverse("dictionary:home"))
        self.assertEqual(response.status_code, 200)

    def test_homepage_contains_branding(self):
        response = self.client.get(reverse("dictionary:home"))
        self.assertContains(response, "शब्दसेतु")
        self.assertContains(response, "ShabdSetu")

    def test_homepage_has_search_form(self):
        response = self.client.get(reverse("dictionary:home"))
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'id="search-input"')

    def test_homepage_has_search_hint(self):
        response = self.client.get(reverse("dictionary:home"))
        self.assertContains(response, "Devanagari")
        self.assertContains(response, "romanised")

    def test_homepage_has_about_section(self):
        response = self.client.get(reverse("dictionary:home"))
        self.assertContains(response, "How it works")


class SearchResultsTests(ViewTestMixin, TestCase):
    """Tests for search results displayed on the homepage."""

    def test_search_exact_devanagari(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "शिक्षा"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "शिक्षा")
        self.assertContains(response, "śikṣā")

    def test_search_preserves_query(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "shiksha"})
        self.assertContains(response, 'value="shiksha"')

    def test_search_exact_romanised(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "prakash"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "प्रकाश")

    def test_search_case_insensitive(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "PRAKASH"})
        self.assertContains(response, "प्रकाश")

    def test_search_shows_meanings(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "shiksha"})
        self.assertContains(response, "education")

    def test_search_shows_pos(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "shiksha"})
        # POS display from get_pos_display
        content = response.content.decode()
        self.assertTrue("Noun" in content or "noun" in content.lower())

    def test_search_results_are_clickable(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "shiksha"})
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        detail_url = reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        self.assertContains(response, detail_url)

    def test_fuzzy_marked_as_suggestion(self):
        response = self.client.get(reverse("dictionary:home"), {"q": "shikshaa"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "शिक्षा")
        self.assertContains(response, "Suggestion")

    def test_fuzzy_not_shown_as_exact(self):
        """Fuzzy results must not use the exact match badge."""
        response = self.client.get(reverse("dictionary:home"), {"q": "shikshaa"})
        content = response.content.decode()
        # Should have fuzzy badge, not exact badge (for this match)
        self.assertIn("result-badge--fuzzy", content)


class NoResultsTests(ViewTestMixin, TestCase):
    """Tests for the no-results state."""

    def test_no_results_message(self):
        response = self.client.get(
            reverse("dictionary:home"), {"q": "xyz123abcdef"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No entries found")
        self.assertContains(response, "xyz123abcdef")

    def test_no_results_preserves_query(self):
        response = self.client.get(
            reverse("dictionary:home"), {"q": "nonexistent"}
        )
        self.assertContains(response, 'value="nonexistent"')

    def test_no_results_has_tips(self):
        response = self.client.get(
            reverse("dictionary:home"), {"q": "xyz123abcdef"}
        )
        self.assertContains(response, "spelling")

    def test_empty_query_shows_homepage(self):
        response = self.client.get(reverse("dictionary:home"), {"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How it works")


class WordDetailTests(ViewTestMixin, TestCase):
    """Tests for the word detail page."""

    def test_detail_page_loads(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_shows_headword(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertContains(response, "शिक्षा")

    def test_detail_shows_transliteration(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertContains(response, "śikṣā")

    def test_detail_shows_meanings(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertContains(response, "education")
        self.assertContains(response, "learning")

    def test_detail_shows_example(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertContains(response, "शिक्षा हर बच्चे का अधिकार है")

    def test_detail_shows_variants(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertContains(response, "shiksha")
        self.assertContains(response, "siksha")

    def test_detail_shows_pos(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        content = response.content.decode()
        self.assertTrue("Noun" in content or "noun" in content.lower())

    def test_detail_has_back_link(self):
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertContains(response, reverse("dictionary:home"))

    def test_detail_404_for_nonexistent(self):
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": 99999})
        )
        self.assertEqual(response.status_code, 404)


class FullUserJourneyTests(ViewTestMixin, TestCase):
    """Integration tests for the complete user flow."""

    def test_homepage_to_search_to_detail_to_back(self):
        """Homepage → Search → Click result → Detail → Back to search."""
        # 1. Visit homepage.
        response = self.client.get(reverse("dictionary:home"))
        self.assertEqual(response.status_code, 200)

        # 2. Search for a word.
        response = self.client.get(reverse("dictionary:home"), {"q": "karma"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "कर्म")

        # 3. Click through to detail page.
        entry = DictionaryEntry.objects.get(headword="कर्म")
        detail_url = reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "कर्म")
        self.assertContains(response, "action, deed")

        # 4. Back link exists.
        self.assertContains(response, reverse("dictionary:home"))

    def test_fuzzy_search_journey(self):
        """Search with typo → see suggestion → click through to detail."""
        response = self.client.get(
            reverse("dictionary:home"), {"q": "shikshaa"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "शिक्षा")
        self.assertContains(response, "Suggestion")

        # Click through to detail.
        entry = DictionaryEntry.objects.get(headword="शिक्षा")
        response = self.client.get(
            reverse("dictionary:word_detail", kwargs={"pk": entry.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "education")

