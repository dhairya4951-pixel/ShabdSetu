"""
Root URL configuration for the shabdsetu project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("manage/", include("dictionary.admin_urls")),
    path("", include("dictionary.urls")),
]
