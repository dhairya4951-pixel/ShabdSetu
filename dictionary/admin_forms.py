"""
Django forms for the custom admin dashboard.

Handles DictionaryEntry creation and editing with server-side
validation.  Romanised variants and meanings are handled manually
in the views (dynamic field lists via POST arrays).
"""

from django import forms

from dictionary.models import DictionaryEntry


class DictionaryEntryForm(forms.ModelForm):
    """Form for creating and editing dictionary entries."""

    class Meta:
        model = DictionaryEntry
        fields = [
            "headword",
            "transliteration",
            "pos",
            "example",
            "source_name",
            "source_url",
            "is_verified",
        ]
        widgets = {
            "headword": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. पुस्तक",
            }),
            "transliteration": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. pustaka",
            }),
            "pos": forms.Select(attrs={
                "class": "form-select",
            }),
            "example": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Example sentence using the word…",
            }),
            "source_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Monier-Williams Sanskrit Dictionary",
            }),
            "source_url": forms.URLInput(attrs={
                "class": "form-input",
                "placeholder": "https://…",
            }),
            "is_verified": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
            }),
        }

    def clean_headword(self):
        """Strip whitespace from headword."""
        return self.cleaned_data["headword"].strip()

    def clean_transliteration(self):
        """Strip whitespace from transliteration."""
        return self.cleaned_data["transliteration"].strip()


class StaffLoginForm(forms.Form):
    """Simple login form for the staff dashboard."""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Username",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-input",
            "placeholder": "Password",
        }),
    )

