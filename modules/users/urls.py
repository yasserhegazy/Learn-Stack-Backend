"""
URL Configuration for User & Role Management Module

Module-specific API routes.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Router and URL patterns will be defined here following TDD approach

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
]
