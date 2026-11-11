"""
Views for the custom admin dashboard at /manage/.

Provides a complete editorial management interface for dictionary
entries, separate from Django's built-in admin at /admin/.

All views require staff authentication via the ``staff_required``
decorator.  Modifications are protected with POST + CSRF.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from dictionary.admin_forms import DictionaryEntryForm, StaffLoginForm
from dictionary.models import DictionaryEntry, Meaning, RomanisedVariant


# ────────────────────────────────────────────────────────────────
#  Access-control decorator
# ────────────────────────────────────────────────────────────────

def staff_required(view_func):
    """Reject unauthenticated or non-staff users."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            login_url = getattr(settings, "LOGIN_URL", "/manage/login/")
            return redirect(f"{login_url}?next={request.path}")
        if not request.user.is_staff:
            return HttpResponseForbidden(
                "Access denied. Staff privileges required."
            )
        return view_func(request, *args, **kwargs)
    return _wrapped


# ────────────────────────────────────────────────────────────────
#  Authentication
# ────────────────────────────────────────────────────────────────

def manage_login(request):
    """Staff-only login page for the custom dashboard."""
    # Already authenticated staff → go to dashboard.
    if request.user.is_authenticated and request.user.is_staff:
        next_url = request.GET.get("next", "")
        return redirect(next_url or "manage:dashboard")

    form = StaffLoginForm(request.POST or None)
    next_url = request.GET.get("next", "") or request.POST.get("next", "")

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            if user.is_staff:
                login(request, user)
                return redirect(next_url or "manage:dashboard")
            else:
                messages.error(
                    request,
                    "Access denied. Staff privileges required.",
                )
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "dictionary/manage/login.html", {
        "form": form,
        "next": next_url,
    })


def manage_logout(request):
    """Log the current user out (POST only for CSRF safety)."""
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("manage:login")


# ────────────────────────────────────────────────────────────────
#  Dashboard
# ────────────────────────────────────────────────────────────────

@staff_required
def manage_dashboard(request):
    """Main dashboard with aggregate statistics."""
    total_entries = DictionaryEntry.objects.count()
    verified = DictionaryEntry.objects.filter(is_verified=True).count()

    context = {
        "total_entries": total_entries,
        "verified_entries": verified,
        "unverified_entries": total_entries - verified,
        "total_variants": RomanisedVariant.objects.count(),
        "total_meanings": Meaning.objects.count(),
        "recent_added": DictionaryEntry.objects.order_by("-created_at")[:5],
        "recent_updated": DictionaryEntry.objects.order_by("-updated_at")[:5],
        "active_nav": "dashboard",
    }
    return render(request, "dictionary/manage/dashboard.html", context)


# ────────────────────────────────────────────────────────────────
#  Entry list
# ────────────────────────────────────────────────────────────────

@staff_required
def manage_entries(request):
    """Paginated, searchable, filterable list of all entries."""
    qs = DictionaryEntry.objects.prefetch_related(
        "romanised_variants", "meaning_items",
    )

    # ── Search ──
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(headword__icontains=q)
            | Q(transliteration__icontains=q)
            | Q(romanised_variants__spelling__icontains=q)
        ).distinct()

    # ── POS filter ──
    pos_filter = request.GET.get("pos", "")
    if pos_filter:
        qs = qs.filter(pos=pos_filter)

    # ── Verification filter ──
    verified_filter = request.GET.get("verified", "")
    if verified_filter == "yes":
        qs = qs.filter(is_verified=True)
    elif verified_filter == "no":
        qs = qs.filter(is_verified=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "page_obj": page_obj,
        "query": q,
        "pos_filter": pos_filter,
        "verified_filter": verified_filter,
        "pos_choices": DictionaryEntry.POS_CHOICES,
        "active_nav": "entries",
    }
    return render(request, "dictionary/manage/entries.html", context)


# ────────────────────────────────────────────────────────────────
#  Create entry
# ────────────────────────────────────────────────────────────────

@staff_required
def manage_entry_create(request):
    """Create a new dictionary entry with variants and meanings."""
    if request.method == "POST":
        form = DictionaryEntryForm(request.POST)
        variants = _clean_list(request.POST.getlist("variant_spelling"))
        meaning_texts = _clean_list(request.POST.getlist("meaning_text"))

        if form.is_valid() and meaning_texts:
            try:
                with transaction.atomic():
                    entry = form.save()
                    _save_variants(entry, variants)
                    _save_meanings(entry, meaning_texts)
                messages.success(
                    request,
                    f"Entry \u201c{entry.headword}\u201d created successfully.",
                )
                return redirect("manage:entry_detail", pk=entry.pk)
            except IntegrityError as exc:
                messages.error(request, f"Database error: {exc}")
        else:
            if not meaning_texts:
                messages.error(request, "At least one meaning is required.")
        # Preserve entered data on validation failure.
        raw_variants = request.POST.getlist("variant_spelling")
        raw_meanings = request.POST.getlist("meaning_text")
    else:
        form = DictionaryEntryForm()
        raw_variants = [""]
        raw_meanings = [""]

    return render(request, "dictionary/manage/entry_form.html", {
        "form": form,
        "variants": raw_variants or [""],
        "meaning_texts": raw_meanings or [""],
        "is_edit": False,
        "active_nav": "create",
    })


# ────────────────────────────────────────────────────────────────
#  Entry detail (admin preview)
# ────────────────────────────────────────────────────────────────

@staff_required
def manage_entry_detail(request, pk):
    """Staff-only preview of a single entry."""
    entry = get_object_or_404(DictionaryEntry, pk=pk)
    pos_display = dict(DictionaryEntry.POS_CHOICES).get(entry.pos, entry.pos)

    return render(request, "dictionary/manage/entry_detail.html", {
        "entry": entry,
        "meanings": entry.meaning_items.all(),
        "variants": entry.romanised_variants.all(),
        "pos_display": pos_display,
        "active_nav": "entries",
    })


# ────────────────────────────────────────────────────────────────
#  Edit entry
# ────────────────────────────────────────────────────────────────

@staff_required
def manage_entry_edit(request, pk):
    """Edit an existing entry, its variants and meanings."""
    entry = get_object_or_404(DictionaryEntry, pk=pk)

    if request.method == "POST":
        form = DictionaryEntryForm(request.POST, instance=entry)
        variants = _clean_list(request.POST.getlist("variant_spelling"))
        meaning_texts = _clean_list(request.POST.getlist("meaning_text"))

        if form.is_valid() and meaning_texts:
            try:
                with transaction.atomic():
                    entry = form.save()
                    # Replace variants and meanings atomically.
                    entry.romanised_variants.all().delete()
                    entry.meaning_items.all().delete()
                    _save_variants(entry, variants)
                    _save_meanings(entry, meaning_texts)
                messages.success(
                    request,
                    f"Entry \u201c{entry.headword}\u201d updated successfully.",
                )
                return redirect("manage:entry_detail", pk=entry.pk)
            except IntegrityError as exc:
                messages.error(request, f"Database error: {exc}")
        else:
            if not meaning_texts:
                messages.error(request, "At least one meaning is required.")
        raw_variants = request.POST.getlist("variant_spelling")
        raw_meanings = request.POST.getlist("meaning_text")
    else:
        form = DictionaryEntryForm(instance=entry)
        raw_variants = list(
            entry.romanised_variants.values_list("spelling", flat=True)
        )
        raw_meanings = list(
            entry.meaning_items.values_list("text", flat=True)
        )

    return render(request, "dictionary/manage/entry_form.html", {
        "form": form,
        "entry": entry,
        "variants": raw_variants or [""],
        "meaning_texts": raw_meanings or [""],
        "is_edit": True,
        "active_nav": "entries",
    })


# ────────────────────────────────────────────────────────────────
#  Delete entry
# ────────────────────────────────────────────────────────────────

@staff_required
def manage_entry_delete(request, pk):
    """Delete confirmation + actual deletion (POST only)."""
    entry = get_object_or_404(DictionaryEntry, pk=pk)

    if request.method == "POST":
        headword = entry.headword
        entry.delete()
        messages.success(
            request, f"Entry \u201c{headword}\u201d deleted successfully."
        )
        return redirect("manage:entries")

    return render(request, "dictionary/manage/entry_delete.html", {
        "entry": entry,
        "active_nav": "entries",
    })


# ────────────────────────────────────────────────────────────────
#  Verification management
# ────────────────────────────────────────────────────────────────

@staff_required
def manage_verification(request):
    """List entries by verification status for editorial review."""
    show = request.GET.get("show", "unverified")

    if show == "all":
        qs = DictionaryEntry.objects.all()
    elif show == "verified":
        qs = DictionaryEntry.objects.filter(is_verified=True)
    else:
        show = "unverified"                     # normalise
        qs = DictionaryEntry.objects.filter(is_verified=False)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "dictionary/manage/verification.html", {
        "page_obj": page_obj,
        "show": show,
        "active_nav": "verification",
    })


@staff_required
@require_POST
def manage_toggle_verify(request, pk):
    """Toggle the verification flag on a single entry (POST only)."""
    entry = get_object_or_404(DictionaryEntry, pk=pk)
    entry.is_verified = not entry.is_verified
    entry.save(update_fields=["is_verified", "updated_at"])

    label = "verified" if entry.is_verified else "unverified"
    messages.success(
        request, f"Entry \u201c{entry.headword}\u201d marked as {label}."
    )

    next_url = request.POST.get("next", "")
    return redirect(next_url or "manage:verification")


# ────────────────────────────────────────────────────────────────
#  Private helpers
# ────────────────────────────────────────────────────────────────

def _clean_list(raw):
    """Return a list of non-empty stripped strings."""
    return [s.strip() for s in raw if s.strip()]


def _save_variants(entry, spellings):
    """Create RomanisedVariant rows, skipping duplicates."""
    seen = set()
    for spelling in spellings:
        key = spelling.lower()
        if key not in seen:
            seen.add(key)
            RomanisedVariant.objects.create(entry=entry, spelling=spelling)


def _save_meanings(entry, texts):
    """Create Meaning rows in display order."""
    for position, text in enumerate(texts, start=1):
        Meaning.objects.create(entry=entry, text=text, position=position)

