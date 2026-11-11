"""
URL patterns for the custom admin dashboard at /manage/.

Kept separate from the public dictionary URLs in urls.py.
"""

from django.urls import path

from dictionary import admin_views

app_name = "manage"

urlpatterns = [
    # Authentication
    path("login/", admin_views.manage_login, name="login"),
    path("logout/", admin_views.manage_logout, name="logout"),

    # Dashboard
    path("", admin_views.manage_dashboard, name="dashboard"),

    # Entry management
    path("entries/", admin_views.manage_entries, name="entries"),
    path("entries/new/", admin_views.manage_entry_create, name="entry_create"),
    path("entries/<int:pk>/", admin_views.manage_entry_detail, name="entry_detail"),
    path("entries/<int:pk>/edit/", admin_views.manage_entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", admin_views.manage_entry_delete, name="entry_delete"),
    path("entries/<int:pk>/verify/", admin_views.manage_toggle_verify, name="toggle_verify"),

    # Verification management
    path("verification/", admin_views.manage_verification, name="verification"),
]

