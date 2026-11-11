"""
Dictionary models for ShabdSetu.

Three models capture the core data:
- DictionaryEntry: the headword and its metadata.
- RomanisedVariant: alternate romanised spellings users might search for.
- Meaning: one or more definitions attached to an entry.
"""

from django.db import models


class DictionaryEntry(models.Model):
    """
    A single dictionary headword in Devanagari with its transliteration,
    part of speech, example usage, and source attribution.
    """

    POS_CHOICES = [
        ("noun", "Noun (संज्ञा)"),
        ("verb", "Verb (क्रिया)"),
        ("adj", "Adjective (विशेषण)"),
        ("adv", "Adverb (क्रिया विशेषण)"),
        ("pron", "Pronoun (सर्वनाम)"),
        ("prep", "Postposition (परसर्ग)"),
        ("conj", "Conjunction (समुच्चयबोधक)"),
        ("intj", "Interjection (विस्मयादिबोधक)"),
        ("part", "Particle (अव्यय)"),
    ]

    headword = models.CharField(
        max_length=128,
        unique=True,
        help_text="The word in Devanagari script, e.g. पुस्तक",
    )
    transliteration = models.CharField(
        max_length=128,
        help_text="IAST transliteration, e.g. pustaka",
    )
    pos = models.CharField(
        max_length=8,
        choices=POS_CHOICES,
        verbose_name="part of speech",
        help_text="Grammatical category of the word.",
    )
    example = models.TextField(
        blank=True,
        default="",
        help_text="Example sentence using the headword.",
    )

    # Source attribution — optional but encouraged for data quality.
    source_name = models.CharField(
        max_length=256,
        blank=True,
        default="",
        verbose_name="source name",
        help_text="Name of the dictionary or corpus this entry was taken from.",
    )
    source_url = models.URLField(
        blank=True,
        default="",
        verbose_name="source URL",
        help_text="Link to the original source, if available.",
    )

    # Data-quality flag.  Must be set manually by a human editor.
    is_verified = models.BooleanField(
        default=False,
        help_text="Checked by a human editor. Never auto-set by imports.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["headword"]
        verbose_name = "dictionary entry"
        verbose_name_plural = "dictionary entries"

    def __str__(self):
        return f"{self.headword} ({self.transliteration})"


class RomanisedVariant(models.Model):
    """
    An alternate romanised spelling that maps to a DictionaryEntry.

    Users might type "pustak", "pustaka", or "kitab" — each variant
    points back to the canonical Devanagari headword so the search
    engine can resolve any of them.
    """

    entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name="romanised_variants",
    )
    spelling = models.CharField(
        max_length=128,
        help_text="A romanised spelling variant, e.g. pustak",
    )

    class Meta:
        ordering = ["spelling"]
        verbose_name = "romanised variant"
        verbose_name_plural = "romanised variants"
        constraints = [
            models.UniqueConstraint(
                fields=["entry", "spelling"],
                name="unique_variant_per_entry",
            ),
        ]

    def __str__(self):
        return self.spelling


class Meaning(models.Model):
    """
    A single definition / sense of a DictionaryEntry.

    Multiple meanings are ordered by `position` so the most common
    sense appears first.
    """

    entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name="meaning_items",
    )
    text = models.TextField(
        help_text="The definition text for this sense.",
    )
    position = models.PositiveSmallIntegerField(
        default=1,
        help_text="Display order (1 = primary meaning).",
    )

    class Meta:
        ordering = ["position"]
        verbose_name = "meaning"
        verbose_name_plural = "meanings"

    def __str__(self):
        # Truncate long definitions in admin lists.
        preview = self.text[:60] + "…" if len(self.text) > 60 else self.text
        return f"{self.position}. {preview}"
