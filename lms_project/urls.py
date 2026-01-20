"""
URL configuration for LMS Project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView, TokenVerifyView)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API v1
    path(
        "api/v1/",
        include(
            [
                # Authentication endpoints
                path(
                    "auth/",
                    include(
                        [
                            path(
                                "token/",
                                TokenObtainPairView.as_view(),
                                name="token_obtain_pair",
                            ),
                            path(
                                "token/refresh/",
                                TokenRefreshView.as_view(),
                                name="token_refresh",
                            ),
                            path(
                                "token/verify/",
                                TokenVerifyView.as_view(),
                                name="token_verify",
                            ),
                        ]
                    ),
                ),
                # Module routes
                path("users/", include("modules.users.urls")),
                # path('courses/', include('modules.courses.urls')),
                # path('assessments/', include('modules.assessments.urls')),
                # path('certifications/', include('modules.certifications.urls')),
                # path('analytics/', include('modules.analytics.urls')),
                # path('communications/', include('modules.communications.urls')),
            ]
        ),
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
