"""
Management command to import dictionary entries from entries.json.

Usage:
    python manage.py import_dictionary
    python manage.py import_dictionary --update-existing

Safe to run multiple times.  Without --update-existing, entries whose
headword already exists in the database are skipped — this protects
edits made through Django Admin.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dictionary.models import DictionaryEntry, Meaning, RomanisedVariant

# Path to the canonical data file, relative to this command file.
DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "entries.json"

# Fields that every entry must contain.
REQUIRED_FIELDS = {"id", "headword", "transliteration", "pos", "meanings"}

# Valid POS values (keys from the model's POS_CHOICES).
VALID_POS = {code for code, _label in DictionaryEntry.POS_CHOICES}

# ---------------------------------------------------------------------------
# POS normalisation
# ---------------------------------------------------------------------------
# The Garuda dataset uses POS strings like "noun (m.)" and "noun (f.)".
# Our model stores a short code ("noun", "verb", etc.).
# This mapping normalises the source format to our model's POS_CHOICES.
POS_MAP = {
    "noun": "noun",
    "noun (m.)": "noun",
    "noun (f.)": "noun",
    "noun (n.)": "noun",
    "verb": "verb",
    "adjective": "adj",
    "adj": "adj",
    "adverb": "adv",
    "adv": "adv",
    "pronoun": "pron",
    "pron": "pron",
    "postposition": "prep",
    "prep": "prep",
    "conjunction": "conj",
    "conj": "conj",
    "interjection": "intj",
    "intj": "intj",
    "particle": "part",
    "part": "part",
}


def normalise_pos(raw_pos: str) -> str | None:
    """
    Convert a POS string from the data file to a model POS code.

    Returns the normalised code, or None if it cannot be mapped.
    """
    key = raw_pos.strip().lower()
    return POS_MAP.get(key)


class Command(BaseCommand):
    help = "Import dictionary entries from dictionary/data/entries.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update-existing",
            action="store_true",
            default=False,
            help=(
                "Update entries that already exist in the database.  "
                "Without this flag, existing entries are skipped to "
                "protect edits made through Django Admin."
            ),
        )
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to a JSON file to import (defaults to dictionary/data/entries.json).",
        )

    def handle(self, *args, **options):
        update_existing = options["update_existing"]
        file_path = Path(options["file"]) if options["file"] else DATA_FILE

        # ------------------------------------------------------------------
        # 1. Read and parse the data file.
        # ------------------------------------------------------------------
        if not file_path.exists():
            raise CommandError(f"Data file not found: {file_path}")

        try:
            raw = file_path.read_text(encoding="utf-8")
            entries_data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {file_path}: {exc}")

        if not isinstance(entries_data, list):
            raise CommandError("The JSON file must contain a top-level array.")

        self.stdout.write(f"Found {len(entries_data)} entries in {file_path.name}")

        # ------------------------------------------------------------------
        # 2. Validate every entry before touching the database.
        # ------------------------------------------------------------------
        for idx, entry in enumerate(entries_data):
            self._validate_entry(entry, idx)

        # ------------------------------------------------------------------
        # 3. Import inside a single transaction.
        # ------------------------------------------------------------------
        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for entry in entries_data:
                result = self._import_entry(entry, update_existing)
                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

        # ------------------------------------------------------------------
        # 4. Report results.
        # ------------------------------------------------------------------
        parts = []
        if created:
            parts.append(self.style.SUCCESS(f"{created} created"))
        if updated:
            parts.append(self.style.WARNING(f"{updated} updated"))
        if skipped:
            parts.append(f"{skipped} skipped (already exist)")

        self.stdout.write("Import complete: " + ", ".join(parts) + ".")

    # ======================================================================
    # Helpers
    # ======================================================================

    def _validate_entry(self, entry: dict, idx: int) -> None:
        """Raise CommandError if a required field is missing or invalid."""
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            raise CommandError(
                f"Entry #{idx + 1} is missing required fields: {', '.join(sorted(missing))}"
            )

        if not entry["headword"].strip():
            raise CommandError(f"Entry #{idx + 1} has an empty headword.")

        pos_code = normalise_pos(entry["pos"])
        if pos_code is None:
            raise CommandError(
                f"Entry #{idx + 1} ({entry['headword']}): "
                f"unrecognised POS '{entry['pos']}'. "
                f"Known values: {', '.join(sorted(POS_MAP.keys()))}"
            )

        if not isinstance(entry["meanings"], list) or len(entry["meanings"]) == 0:
            raise CommandError(
                f"Entry #{idx + 1} ({entry['headword']}): "
                f"'meanings' must be a non-empty list."
            )

    def _import_entry(self, data: dict, update_existing: bool) -> str:
        """
        Create or update a single DictionaryEntry and its related objects.

        Returns 'created', 'updated', or 'skipped'.
        """
        headword = data["headword"].strip()
        pos_code = normalise_pos(data["pos"])
        existing = DictionaryEntry.objects.filter(headword=headword).first()

        if existing and not update_existing:
            self.stdout.write(f"  ⏭  {headword} — already exists, skipping.")
            return "skipped"

        if existing and update_existing:
            entry = existing
            entry.transliteration = data["transliteration"]
            entry.pos = pos_code
            entry.example = data.get("example", "")
            # Never touch is_verified — that's for human editors only.
            entry.save()
            self._sync_meanings(entry, data["meanings"])
            self._sync_variants(entry, data.get("romanised", []))
            self.stdout.write(f"  🔄 {headword} — updated.")
            return "updated"

        # Create new entry.
        entry = DictionaryEntry.objects.create(
            headword=headword,
            transliteration=data["transliteration"],
            pos=pos_code,
            example=data.get("example", ""),
            # is_verified intentionally left False.
        )
        self._sync_meanings(entry, data["meanings"])
        self._sync_variants(entry, data.get("romanised", []))
        self.stdout.write(f"  ✅ {headword} — created.")
        return "created"

    def _sync_meanings(self, entry: DictionaryEntry, meanings: list[str]) -> None:
        """Replace all meanings with those from the data file."""
        entry.meaning_items.all().delete()
        for position, text in enumerate(meanings, start=1):
            Meaning.objects.create(entry=entry, text=text.strip(), position=position)

    def _sync_variants(self, entry: DictionaryEntry, variants: list[str]) -> None:
        """Ensure every variant in the list exists; don't remove extras
        that may have been added through Django Admin."""
        for spelling in variants:
            spelling = spelling.strip().lower()
            if spelling:
                RomanisedVariant.objects.get_or_create(
                    entry=entry,
                    spelling=spelling,
                )
