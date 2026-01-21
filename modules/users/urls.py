"""URL configuration for users module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from modules.users.views import (
    CustomTokenObtainPairView,
    RoleViewSet,
    TenantViewSet,
    UserViewSet,
)

app_name = "users"

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"tenants", TenantViewSet, basename="tenant")

# UserViewSet will be included separately to avoid /users/users/ pattern
user_list = UserViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

user_detail = UserViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

user_me = UserViewSet.as_view({
    'get': 'me'
})

user_change_password = UserViewSet.as_view({
    'post': 'change_password'
})

user_assign_role = UserViewSet.as_view({
    'post': 'assign_role'
})

user_remove_role = UserViewSet.as_view({
    'post': 'remove_role'
})

urlpatterns = [
    # Auth endpoints
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    
    # User endpoints (avoiding /users/users/ pattern)
    path("", user_list, name="user-list"),
    path("me/", user_me, name="user-me"),
    path("change_password/", user_change_password, name="user-change-password"),
    path("<int:pk>/", user_detail, name="user-detail"),
    path("<int:pk>/assign_role/", user_assign_role, name="user-assign-role"),
    path("<int:pk>/remove_role/", user_remove_role, name="user-remove-role"),
    
    # Role and Tenant endpoints (using router)
    path("", include(router.urls)),
]
