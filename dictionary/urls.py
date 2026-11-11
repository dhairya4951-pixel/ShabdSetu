"""
URL patterns for the dictionary app.
"""

from django.urls import path

from . import views

app_name = "dictionary"

urlpatterns = [
    path("", views.home, name="home"),
    path("word/<int:pk>/", views.word_detail, name="word_detail"),
]
