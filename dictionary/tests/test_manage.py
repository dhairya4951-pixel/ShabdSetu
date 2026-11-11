"""
Tests for the custom admin dashboard at /manage/.

Covers authentication, access control, CRUD operations on
dictionary entries, verification management, and search/filters.
"""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from dictionary.models import DictionaryEntry, Meaning, RomanisedVariant


def _make_entry(**kwargs):
    """Helper: create a DictionaryEntry with sensible defaults."""
    defaults = {
        "headword": "शिक्षा",
        "transliteration": "śikṣā",
        "pos": "noun",
        "example": "शिक्षा हर बच्चे का अधिकार है।",
    }
    defaults.update(kwargs)
    return DictionaryEntry.objects.create(**defaults)


@override_settings(LOGIN_URL="/manage/login/")
class AuthenticationTests(TestCase):
    """Staff-only access control for /manage/."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.normal = User.objects.create_user(
            "visitor", password="pass1234", is_staff=False,
        )

    # ── Unauthenticated users ──

    def test_unauthenticated_redirected_to_login(self):
        """Anonymous users are sent to the login page."""
        resp = self.client.get(reverse("manage:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/manage/login/", resp.url)

    def test_unauthenticated_cannot_access_entries(self):
        resp = self.client.get(reverse("manage:entries"))
        self.assertEqual(resp.status_code, 302)

    def test_unauthenticated_cannot_access_create(self):
        resp = self.client.get(reverse("manage:entry_create"))
        self.assertEqual(resp.status_code, 302)

    # ── Non-staff users ──

    def test_non_staff_gets_403(self):
        """Authenticated non-staff users receive a 403 Forbidden."""
        self.client.login(username="visitor", password="pass1234")
        resp = self.client.get(reverse("manage:dashboard"))
        self.assertEqual(resp.status_code, 403)

    def test_non_staff_cannot_access_entries(self):
        self.client.login(username="visitor", password="pass1234")
        resp = self.client.get(reverse("manage:entries"))
        self.assertEqual(resp.status_code, 403)

    # ── Staff users ──

    def test_staff_can_access_dashboard(self):
        """Staff users see the dashboard."""
        self.client.login(username="editor", password="pass1234")
        resp = self.client.get(reverse("manage:dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_staff_login_flow(self):
        """POST valid credentials → redirect to dashboard."""
        resp = self.client.post(reverse("manage:login"), {
            "username": "editor",
            "password": "pass1234",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("manage:dashboard"), resp.url)

    def test_invalid_login_shows_error(self):
        """Wrong password keeps the user on the login page."""
        resp = self.client.post(reverse("manage:login"), {
            "username": "editor",
            "password": "wrong",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid username or password")

    def test_non_staff_login_rejected(self):
        """Non-staff user can't log in to the dashboard."""
        resp = self.client.post(reverse("manage:login"), {
            "username": "visitor",
            "password": "pass1234",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Staff privileges required")

    def test_logout_clears_session(self):
        """POST to logout redirects to login."""
        self.client.login(username="editor", password="pass1234")
        resp = self.client.post(reverse("manage:logout"))
        self.assertEqual(resp.status_code, 302)
        # After logout, dashboard should redirect to login.
        resp2 = self.client.get(reverse("manage:dashboard"))
        self.assertEqual(resp2.status_code, 302)


@override_settings(LOGIN_URL="/manage/login/")
class DashboardTests(TestCase):
    """Dashboard statistics from real data."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.client.login(username="editor", password="pass1234")

    def test_dashboard_shows_stats(self):
        _make_entry(headword="शब्द", transliteration="śabda")
        _make_entry(headword="भाषा", transliteration="bhāṣā", is_verified=True)
        resp = self.client.get(reverse("manage:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["total_entries"], 2)
        self.assertEqual(resp.context["verified_entries"], 1)
        self.assertEqual(resp.context["unverified_entries"], 1)


@override_settings(LOGIN_URL="/manage/login/")
class EntryCreateTests(TestCase):
    """Creating dictionary entries through the dashboard."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.client.login(username="editor", password="pass1234")

    def test_create_entry_success(self):
        """Submitting a valid form creates the entry + variants + meanings."""
        resp = self.client.post(reverse("manage:entry_create"), {
            "headword": "शिक्षा",
            "transliteration": "śikṣā",
            "pos": "noun",
            "example": "शिक्षा हर बच्चे का अधिकार है।",
            "source_name": "",
            "source_url": "",
            "variant_spelling": ["shiksha", "siksha"],
            "meaning_text": ["education", "learning"],
        })
        self.assertEqual(resp.status_code, 302)                # redirect
        self.assertEqual(DictionaryEntry.objects.count(), 1)

        entry = DictionaryEntry.objects.first()
        self.assertEqual(entry.headword, "शिक्षा")
        self.assertEqual(entry.romanised_variants.count(), 2)
        self.assertEqual(entry.meaning_items.count(), 2)

    def test_create_entry_preserves_meaning_order(self):
        """Meanings are stored with correct position values."""
        self.client.post(reverse("manage:entry_create"), {
            "headword": "शब्द",
            "transliteration": "śabda",
            "pos": "noun",
            "variant_spelling": ["shabd"],
            "meaning_text": ["word", "sound"],
        })
        meanings = list(
            Meaning.objects.filter(entry__headword="शब्द")
            .order_by("position")
            .values_list("text", flat=True)
        )
        self.assertEqual(meanings, ["word", "sound"])

    def test_create_entry_requires_meaning(self):
        """Form rejected when no meaning is provided."""
        resp = self.client.post(reverse("manage:entry_create"), {
            "headword": "शब्द",
            "transliteration": "śabda",
            "pos": "noun",
            "variant_spelling": ["shabd"],
            "meaning_text": [""],           # empty
        })
        self.assertEqual(resp.status_code, 200)     # re-renders form
        self.assertEqual(DictionaryEntry.objects.count(), 0)

    def test_create_duplicate_headword_rejected(self):
        """Cannot create two entries with the same headword."""
        _make_entry()
        resp = self.client.post(reverse("manage:entry_create"), {
            "headword": "शिक्षा",           # already exists
            "transliteration": "śikṣā",
            "pos": "noun",
            "variant_spelling": ["shiksha"],
            "meaning_text": ["education"],
        })
        self.assertEqual(resp.status_code, 200)     # form error
        self.assertEqual(DictionaryEntry.objects.count(), 1)

    def test_create_skips_empty_variants(self):
        """Blank variant fields are silently ignored."""
        self.client.post(reverse("manage:entry_create"), {
            "headword": "कर्म",
            "transliteration": "karma",
            "pos": "noun",
            "variant_spelling": ["karma", "", "  "],
            "meaning_text": ["action"],
        })
        entry = DictionaryEntry.objects.get(headword="कर्म")
        self.assertEqual(entry.romanised_variants.count(), 1)


@override_settings(LOGIN_URL="/manage/login/")
class EntryEditTests(TestCase):
    """Editing existing entries."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.client.login(username="editor", password="pass1234")
        self.entry = _make_entry()
        Meaning.objects.create(entry=self.entry, text="education", position=1)
        RomanisedVariant.objects.create(entry=self.entry, spelling="shiksha")

    def test_edit_page_loads_with_existing_data(self):
        resp = self.client.get(
            reverse("manage:entry_edit", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "शिक्षा")
        self.assertContains(resp, "shiksha")
        self.assertContains(resp, "education")

    def test_edit_updates_entry(self):
        resp = self.client.post(
            reverse("manage:entry_edit", kwargs={"pk": self.entry.pk}),
            {
                "headword": "शिक्षा",
                "transliteration": "śikṣā",
                "pos": "noun",
                "example": "Updated example.",
                "source_name": "",
                "source_url": "",
                "variant_spelling": ["shiksha", "siksha"],
                "meaning_text": ["education", "learning"],
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.example, "Updated example.")
        self.assertEqual(self.entry.romanised_variants.count(), 2)
        self.assertEqual(self.entry.meaning_items.count(), 2)

    def test_edit_replaces_variants_and_meanings(self):
        """Editing completely replaces related objects."""
        self.client.post(
            reverse("manage:entry_edit", kwargs={"pk": self.entry.pk}),
            {
                "headword": "शिक्षा",
                "transliteration": "śikṣā",
                "pos": "noun",
                "variant_spelling": ["newvar"],
                "meaning_text": ["new meaning"],
            },
        )
        self.entry.refresh_from_db()
        variants = list(
            self.entry.romanised_variants.values_list("spelling", flat=True)
        )
        self.assertEqual(variants, ["newvar"])
        meanings = list(
            self.entry.meaning_items.values_list("text", flat=True)
        )
        self.assertEqual(meanings, ["new meaning"])


@override_settings(LOGIN_URL="/manage/login/")
class EntryDeleteTests(TestCase):
    """Safe deletion of entries."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.client.login(username="editor", password="pass1234")
        self.entry = _make_entry()

    def test_get_shows_confirmation(self):
        """GET to the delete URL shows confirmation, does NOT delete."""
        resp = self.client.get(
            reverse("manage:entry_delete", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Are you sure")
        self.assertEqual(DictionaryEntry.objects.count(), 1)

    def test_post_deletes_entry(self):
        """POST actually deletes the entry and redirects."""
        resp = self.client.post(
            reverse("manage:entry_delete", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(DictionaryEntry.objects.count(), 0)

    def test_get_does_not_delete(self):
        """Explicit check: GET must never delete."""
        self.client.get(
            reverse("manage:entry_delete", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(DictionaryEntry.objects.count(), 1)


@override_settings(LOGIN_URL="/manage/login/")
class VerificationTests(TestCase):
    """Verification status management."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.client.login(username="editor", password="pass1234")
        self.entry = _make_entry(is_verified=False)

    def test_verification_page_loads(self):
        resp = self.client.get(reverse("manage:verification"))
        self.assertEqual(resp.status_code, 200)

    def test_toggle_verify_marks_entry(self):
        """POST toggles is_verified from False to True."""
        resp = self.client.post(
            reverse("manage:toggle_verify", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(resp.status_code, 302)
        self.entry.refresh_from_db()
        self.assertTrue(self.entry.is_verified)

    def test_toggle_unverify(self):
        """POST toggles is_verified from True to False."""
        self.entry.is_verified = True
        self.entry.save()
        self.client.post(
            reverse("manage:toggle_verify", kwargs={"pk": self.entry.pk})
        )
        self.entry.refresh_from_db()
        self.assertFalse(self.entry.is_verified)

    def test_get_cannot_toggle_verify(self):
        """GET to toggle_verify is not allowed (405)."""
        resp = self.client.get(
            reverse("manage:toggle_verify", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(resp.status_code, 405)

    def test_verification_filter_unverified(self):
        _make_entry(headword="सत्य", transliteration="satya", is_verified=True)
        resp = self.client.get(
            reverse("manage:verification") + "?show=unverified"
        )
        entries = resp.context["page_obj"].object_list
        for e in entries:
            self.assertFalse(e.is_verified)

    def test_verification_filter_verified(self):
        _make_entry(headword="सत्य", transliteration="satya", is_verified=True)
        resp = self.client.get(
            reverse("manage:verification") + "?show=verified"
        )
        entries = resp.context["page_obj"].object_list
        for e in entries:
            self.assertTrue(e.is_verified)


@override_settings(LOGIN_URL="/manage/login/")
class EntrySearchFilterTests(TestCase):
    """Search and filter functionality on the entries list."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.client.login(username="editor", password="pass1234")

        self.e1 = _make_entry(headword="शिक्षा", transliteration="śikṣā")
        self.e2 = _make_entry(headword="भाषा", transliteration="bhāṣā", pos="noun")
        self.e3 = _make_entry(headword="कर्म", transliteration="karma", pos="noun", is_verified=True)

        RomanisedVariant.objects.create(entry=self.e1, spelling="shiksha")

    def test_search_by_headword(self):
        resp = self.client.get(reverse("manage:entries") + "?q=शिक्षा")
        entries = resp.context["page_obj"].object_list
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].headword, "शिक्षा")

    def test_search_by_variant(self):
        resp = self.client.get(reverse("manage:entries") + "?q=shiksha")
        entries = resp.context["page_obj"].object_list
        self.assertEqual(len(entries), 1)

    def test_filter_by_verified(self):
        resp = self.client.get(reverse("manage:entries") + "?verified=yes")
        entries = resp.context["page_obj"].object_list
        self.assertTrue(all(e.is_verified for e in entries))

    def test_filter_by_unverified(self):
        resp = self.client.get(reverse("manage:entries") + "?verified=no")
        entries = resp.context["page_obj"].object_list
        self.assertTrue(all(not e.is_verified for e in entries))

    def test_empty_search_returns_all(self):
        resp = self.client.get(reverse("manage:entries") + "?q=")
        entries = resp.context["page_obj"].object_list
        self.assertEqual(len(entries), 3)


@override_settings(LOGIN_URL="/manage/login/")
class EntryDetailTests(TestCase):
    """Admin preview of a single entry."""

    def setUp(self):
        self.staff = User.objects.create_user(
            "editor", password="pass1234", is_staff=True,
        )
        self.client.login(username="editor", password="pass1234")
        self.entry = _make_entry()
        Meaning.objects.create(entry=self.entry, text="education", position=1)
        RomanisedVariant.objects.create(entry=self.entry, spelling="shiksha")

    def test_detail_page_loads(self):
        resp = self.client.get(
            reverse("manage:entry_detail", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "शिक्षा")
        self.assertContains(resp, "education")
        self.assertContains(resp, "shiksha")

    def test_detail_has_edit_link(self):
        resp = self.client.get(
            reverse("manage:entry_detail", kwargs={"pk": self.entry.pk})
        )
        edit_url = reverse("manage:entry_edit", kwargs={"pk": self.entry.pk})
        self.assertContains(resp, edit_url)

    def test_detail_404_for_nonexistent(self):
        resp = self.client.get(
            reverse("manage:entry_detail", kwargs={"pk": 99999})
        )
        self.assertEqual(resp.status_code, 404)

