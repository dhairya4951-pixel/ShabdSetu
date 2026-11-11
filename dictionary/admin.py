"""
Django Admin configuration for the dictionary app.

DictionaryEntry is the primary model.  RomanisedVariant and Meaning
are edited inline so an editor can manage everything from one page.
"""

from django.contrib import admin

from .models import DictionaryEntry, Meaning, RomanisedVariant


# ---------------------------------------------------------------------------
# Inline editors
# ---------------------------------------------------------------------------

class RomanisedVariantInline(admin.TabularInline):
    """Inline editor for romanised spelling variants."""

    model = RomanisedVariant
    extra = 1
    min_num = 0
    verbose_name = "romanised variant"
    verbose_name_plural = "romanised variants"


class MeaningInline(admin.TabularInline):
    """Inline editor for meanings / definitions."""

    model = Meaning
    extra = 1
    min_num = 1
    verbose_name = "meaning"
    verbose_name_plural = "meanings"


# ---------------------------------------------------------------------------
# Main model admin
# ---------------------------------------------------------------------------

@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(admin.ModelAdmin):
    """Admin view for dictionary entries with inline variants and meanings."""

    # List page
    list_display = [
        "headword",
        "transliteration",
        "pos",
        "is_verified",
        "updated_at",
    ]
    list_filter = ["pos", "is_verified"]
    search_fields = [
        "headword",
        "transliteration",
        "romanised_variants__spelling",
        "meaning_items__text",
    ]
    list_per_page = 30

    # Detail page
    inlines = [RomanisedVariantInline, MeaningInline]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = [
        (
            None,
            {
                "fields": ["headword", "transliteration", "pos"],
            },
        ),
        (
            "Example usage",
            {
                "fields": ["example"],
                "classes": ["collapse"],
            },
        ),
        (
            "Source attribution",
            {
                "fields": ["source_name", "source_url"],
                "classes": ["collapse"],
                "description": (
                    "Where was this entry sourced from?  "
                    "Helps track data quality."
                ),
            },
        ),
        (
            "Status",
            {
                "fields": ["is_verified", "created_at", "updated_at"],
            },
        ),
    ]
