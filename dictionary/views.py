"""
Views for the dictionary app.

Each view is thin — it delegates search logic to search.py
and passes structured results to templates.
"""

from django.http import Http404
from django.shortcuts import render

from dictionary.models import DictionaryEntry, Meaning
from dictionary.search import search, FUZZY, _base_queryset


def home(request):
    """
    Homepage with the search bar.  Also handles search submissions
    via GET parameter ?q=...
    """
    query = request.GET.get("q", "").strip()
    context = {"query": query}

    if query:
        results = search(query)

        # Separate exact/confident matches from fuzzy suggestions.
        exact_results = [r for r in results if not r.is_suggestion]
        suggestions = [r for r in results if r.is_suggestion]

        context.update({
            "results": results,
            "exact_results": exact_results,
            "suggestions": suggestions,
            "has_results": len(results) > 0,
            "has_exact": len(exact_results) > 0,
        })

    return render(request, "dictionary/home.html", context)


def word_detail(request, pk):
    """
    Individual word detail page.

    Displays all information about a single dictionary entry,
    including all meanings, romanised variants, example, and source.
    """
    try:
        entry = _base_queryset().get(pk=pk)
    except DictionaryEntry.DoesNotExist:
        raise Http404("Word not found.")

    # Get POS display label.
    pos_display = dict(DictionaryEntry.POS_CHOICES).get(entry.pos, entry.pos)

    context = {
        "entry": entry,
        "meanings": entry.meaning_items.all(),
        "variants": entry.romanised_variants.all(),
        "pos_display": pos_display,
    }

    return render(request, "dictionary/detail.html", context)
