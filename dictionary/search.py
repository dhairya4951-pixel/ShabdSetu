"""
Bilingual search engine for ShabdSetu.

All query construction and matching logic lives here.  Views call
``search()`` and receive a list of ``SearchResult`` objects — they
never build ORM queries directly.

Search pipeline (in priority order):
    1. Exact Devanagari headword match.
    2. Exact romanised variant match.
    3. Exact IAST transliteration match.
    4. Unicode-normalised, case-insensitive match.
    5. Normalised transliteration match (IAST diacritics stripped).
    6. Prefix / partial match.
    7. Fuzzy spelling suggestions.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from django.db.models import Prefetch, Q

from rapidfuzz import fuzz, process as fuzz_process

from dictionary.models import DictionaryEntry, Meaning, RomanisedVariant

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum fuzzy-match score (0-100) to consider a candidate.
# Tuned to avoid false positives on short queries while still catching
# plausible typos like "shikshaa".
FUZZY_THRESHOLD = 65

# Minimum query length to attempt fuzzy matching.
# Very short queries (1-2 chars) produce too many false positives.
FUZZY_MIN_QUERY_LENGTH = 3

# Maximum number of fuzzy suggestions to return.
FUZZY_MAX_SUGGESTIONS = 5

# ---------------------------------------------------------------------------
# IAST → informal-Roman normalisation map
# ---------------------------------------------------------------------------
# We deliberately map IAST diacritical characters to their most common
# informal romanised equivalents.  This is NOT a proper transliteration
# scheme — it is a search normalisation that increases recall.
#
# The mappings are applied left-to-right on the lowercased string.
# Multi-character mappings come first so they take priority.

_IAST_NORM_MAP: list[tuple[str, str]] = [
    # Sibilants (must come before single-char vowel rules)
    ("ṣ", "sh"),
    ("ś", "sh"),
    # Retroflex consonants
    ("ṭ", "t"),
    ("ḍ", "d"),
    ("ṇ", "n"),
    # Nasals / special consonants
    ("ñ", "n"),
    ("ṅ", "n"),
    ("ṃ", "m"),
    ("ḥ", "h"),
    # Vowels (long → short)
    ("ā", "a"),
    ("ī", "i"),
    ("ū", "u"),
    ("ṛ", "ri"),
    ("ṝ", "ri"),
    ("ḷ", "l"),
    # Anusvara / chandrabindu (already handled above, but belt-and-braces)
]


def normalise_iast(text: str) -> str:
    """
    Convert an IAST string to a simplified informal Roman form.

    Examples:
        śikṣā  → shiksha
        prakāśa → prakasha
        vṛkṣa  → vriksha
        bhāṣā  → bhasha
        śānti  → shanti
    """
    result = text.lower()
    for src, dst in _IAST_NORM_MAP:
        result = result.replace(src, dst)
    return result


def normalise_query(raw: str) -> str:
    """
    Basic normalisation applied to every incoming query:
    - Unicode NFC normalisation.
    - Strip leading / trailing whitespace.
    - Collapse internal whitespace to a single space.
    - Lowercase.
    """
    text = unicodedata.normalize("NFC", raw)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.lower()
    return text


def _is_devanagari(text: str) -> bool:
    """Return True if the string contains at least one Devanagari character."""
    return any("\u0900" <= ch <= "\u097F" for ch in text)


def _strip_combining(text: str) -> str:
    """Remove Unicode combining marks (accents / diacritics)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


# ---------------------------------------------------------------------------
# IAST ↔ Devanagari via indic-transliteration
# ---------------------------------------------------------------------------

def _iast_to_devanagari(text: str) -> str | None:
    """
    Try to convert an IAST string to Devanagari.

    Returns None if the library is unavailable or the input doesn't
    look like valid IAST.
    """
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        result = transliterate(text, sanscript.IAST, sanscript.DEVANAGARI)
        # Only accept if the result actually contains Devanagari.
        if _is_devanagari(result):
            return result
    except Exception:
        pass
    return None


def _devanagari_to_iast(text: str) -> str | None:
    """Try to convert a Devanagari string to IAST."""
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Search result data structure
# ---------------------------------------------------------------------------

# Match-type constants, ordered by confidence (highest first).
EXACT_DEVANAGARI = "exact_devanagari"
EXACT_ROMANISED = "exact_romanised"
EXACT_IAST = "exact_iast"
NORMALISED = "normalised"
TRANSLITERATION = "transliteration"
PARTIAL = "partial"
FUZZY = "fuzzy"

# Human-readable labels for the frontend.
MATCH_LABELS = {
    EXACT_DEVANAGARI: "Exact match (Devanagari)",
    EXACT_ROMANISED: "Exact match (romanised)",
    EXACT_IAST: "Exact match (IAST)",
    NORMALISED: "Normalised match",
    TRANSLITERATION: "Transliteration match",
    PARTIAL: "Partial match",
    FUZZY: "Suggestion (similar spelling)",
}


@dataclass
class SearchResult:
    """A single search result with its entry and matching metadata."""

    entry: DictionaryEntry
    match_type: str
    confidence: float = 1.0       # 0.0–1.0, where 1.0 = exact
    matched_on: str = ""          # the string the query actually matched

    @property
    def match_label(self) -> str:
        return MATCH_LABELS.get(self.match_type, self.match_type)

    @property
    def is_suggestion(self) -> bool:
        """True when the result is a fuzzy suggestion, not a confirmed match."""
        return self.match_type == FUZZY


# ---------------------------------------------------------------------------
# Core prefetch helper
# ---------------------------------------------------------------------------

def _base_queryset() -> "QuerySet[DictionaryEntry]":
    """
    Return a DictionaryEntry queryset with meanings and variants
    prefetched to avoid N+1 queries.
    """
    return DictionaryEntry.objects.prefetch_related(
        Prefetch(
            "meaning_items",
            queryset=Meaning.objects.order_by("position"),
        ),
        "romanised_variants",
    )


# ---------------------------------------------------------------------------
# Individual search stages
# ---------------------------------------------------------------------------

def _exact_devanagari(query: str) -> list[SearchResult]:
    """Stage 1: Exact Devanagari headword match."""
    if not _is_devanagari(query):
        return []
    entries = _base_queryset().filter(headword=query)
    return [
        SearchResult(entry=e, match_type=EXACT_DEVANAGARI, matched_on=e.headword)
        for e in entries
    ]


def _exact_romanised(query_lower: str) -> list[SearchResult]:
    """Stage 2: Exact match against stored romanised variants."""
    variants = (
        RomanisedVariant.objects
        .filter(spelling__iexact=query_lower)
        .select_related("entry")
    )
    seen: set[int] = set()
    results: list[SearchResult] = []
    for v in variants:
        if v.entry_id not in seen:
            seen.add(v.entry_id)
            # Refetch with prefetch for consistency.
            entry = _base_queryset().get(pk=v.entry_id)
            results.append(
                SearchResult(
                    entry=entry,
                    match_type=EXACT_ROMANISED,
                    matched_on=v.spelling,
                )
            )
    return results


def _exact_iast(query: str) -> list[SearchResult]:
    """Stage 3: Exact IAST transliteration match."""
    entries = _base_queryset().filter(transliteration__iexact=query)
    return [
        SearchResult(
            entry=e,
            match_type=EXACT_IAST,
            matched_on=e.transliteration,
        )
        for e in entries
    ]


def _normalised_match(query_lower: str) -> list[SearchResult]:
    """
    Stage 4 & 5: Unicode-normalised / IAST-normalised matching.

    - Compare stripped-diacritic query against stripped-diacritic
      transliterations.
    - Also compare normalised-IAST transliterations against the query.
    """
    query_stripped = _strip_combining(query_lower)
    results: list[SearchResult] = []
    seen: set[int] = set()

    for entry in _base_queryset():
        if entry.pk in seen:
            continue

        # Normalise the entry's IAST transliteration to informal Roman.
        entry_norm = normalise_iast(entry.transliteration)

        # Check if the normalised IAST matches the query exactly.
        if entry_norm == query_lower:
            seen.add(entry.pk)
            results.append(
                SearchResult(
                    entry=entry,
                    match_type=NORMALISED,
                    confidence=0.95,
                    matched_on=entry.transliteration,
                )
            )
            continue

        # Check if diacritic-stripped transliteration matches
        # diacritic-stripped query.
        entry_stripped = _strip_combining(entry.transliteration.lower())
        if entry_stripped == query_stripped and entry_stripped:
            seen.add(entry.pk)
            results.append(
                SearchResult(
                    entry=entry,
                    match_type=NORMALISED,
                    confidence=0.90,
                    matched_on=entry.transliteration,
                )
            )

    return results


def _transliteration_match(query: str) -> list[SearchResult]:
    """
    Stage 5b: Use indic-transliteration to convert the query to
    Devanagari and see if it matches a headword.
    """
    # Only try if the query looks like it could be IAST (has Latin chars).
    if _is_devanagari(query):
        return []

    dev = _iast_to_devanagari(query)
    if not dev:
        return []

    entries = _base_queryset().filter(headword=dev)
    return [
        SearchResult(
            entry=e,
            match_type=TRANSLITERATION,
            confidence=0.90,
            matched_on=f"{query} → {dev}",
        )
        for e in entries
    ]


def _partial_match(query_lower: str) -> list[SearchResult]:
    """
    Stage 6: Prefix / partial matching against transliterations and
    romanised variants.
    """
    results: list[SearchResult] = []
    seen: set[int] = set()

    # Normalise query for comparison.
    query_norm = normalise_iast(query_lower) if query_lower else query_lower

    for entry in _base_queryset():
        if entry.pk in seen:
            continue

        entry_norm = normalise_iast(entry.transliteration)

        # Check if query is a prefix of the normalised transliteration.
        if entry_norm.startswith(query_norm) and query_norm:
            seen.add(entry.pk)
            results.append(
                SearchResult(
                    entry=entry,
                    match_type=PARTIAL,
                    confidence=0.80,
                    matched_on=entry.transliteration,
                )
            )
            continue

        # Check romanised variants for prefix match.
        for variant in entry.romanised_variants.all():
            if variant.spelling.lower().startswith(query_norm) and query_norm:
                if entry.pk not in seen:
                    seen.add(entry.pk)
                    results.append(
                        SearchResult(
                            entry=entry,
                            match_type=PARTIAL,
                            confidence=0.75,
                            matched_on=variant.spelling,
                        )
                    )
                break

    return results


def _fuzzy_match(
    query_lower: str, exclude_ids: set[int]
) -> list[SearchResult]:
    """
    Stage 7: Fuzzy spelling suggestions using RapidFuzz.

    Compares the query against all romanised variants and normalised
    transliterations.  Returns suggestions, NOT confirmed matches.
    """
    if len(query_lower) < FUZZY_MIN_QUERY_LENGTH:
        return []

    # Build a candidate list: (display_string, entry_id).
    candidates: dict[str, int] = {}
    for entry in _base_queryset():
        if entry.pk in exclude_ids:
            continue

        # Add normalised IAST transliteration as a candidate.
        norm = normalise_iast(entry.transliteration)
        candidates[norm] = entry.pk

        # Add the raw transliteration (lowered).
        candidates[entry.transliteration.lower()] = entry.pk

        # Add all stored romanised variants.
        for variant in entry.romanised_variants.all():
            candidates[variant.spelling.lower()] = entry.pk

    if not candidates:
        return []

    # Run fuzzy matching.
    matches = fuzz_process.extract(
        query_lower,
        list(candidates.keys()),
        scorer=fuzz.ratio,
        limit=FUZZY_MAX_SUGGESTIONS * 2,  # over-fetch then filter
    )

    results: list[SearchResult] = []
    seen: set[int] = set()

    for matched_str, score, _idx in matches:
        if score < FUZZY_THRESHOLD:
            continue

        entry_id = candidates[matched_str]
        if entry_id in seen or entry_id in exclude_ids:
            continue
        seen.add(entry_id)

        entry = _base_queryset().get(pk=entry_id)
        results.append(
            SearchResult(
                entry=entry,
                match_type=FUZZY,
                confidence=round(score / 100.0, 2),
                matched_on=matched_str,
            )
        )

        if len(results) >= FUZZY_MAX_SUGGESTIONS:
            break

    # Sort by confidence descending.
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search(raw_query: str) -> list[SearchResult]:
    """
    Search the dictionary with the given query string.

    Returns a list of SearchResult objects sorted by match quality.
    The pipeline runs stages in priority order and stops accumulating
    exact results early, but always appends fuzzy suggestions if the
    exact stages didn't find anything.

    Usage:
        from dictionary.search import search
        results = search("shiksha")
        for r in results:
            print(r.entry.headword, r.match_type, r.confidence)
    """
    query = normalise_query(raw_query)
    if not query:
        return []

    # Collect results from each stage.
    exact_results: list[SearchResult] = []

    # Stage 1: Exact Devanagari.
    exact_results.extend(_exact_devanagari(query))
    if exact_results:
        return exact_results

    query_lower = query  # already lowercased by normalise_query

    # Stage 2: Exact romanised variant.
    exact_results.extend(_exact_romanised(query_lower))
    if exact_results:
        return exact_results

    # Stage 3: Exact IAST transliteration.
    exact_results.extend(_exact_iast(query))
    if exact_results:
        return exact_results

    # Stage 4-5: Normalised matching.
    normalised_results = _normalised_match(query_lower)
    if normalised_results:
        return normalised_results

    # Stage 5b: Transliteration conversion.
    translit_results = _transliteration_match(query)
    if translit_results:
        return translit_results

    # Stage 6: Prefix / partial.
    partial_results = _partial_match(query_lower)

    # Stage 7: Fuzzy — always run if we don't have exact matches.
    already_found = {r.entry.pk for r in partial_results}
    fuzzy_results = _fuzzy_match(query_lower, exclude_ids=already_found)

    # Combine partial + fuzzy, partial first.
    combined = partial_results + fuzzy_results
    return combined
