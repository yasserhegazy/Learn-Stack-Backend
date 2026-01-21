"""
Permissions for User & Role Management Module

Role-based access control, enforced per tenant.
"""

from rest_framework import permissions

from modules.users.models import UserRole


class IsTenantMember(permissions.BasePermission):
    """Permission to check if user belongs to the request's tenant."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        return request.user.tenant_id == tenant.id


class IsAdminRole(permissions.BasePermission):
    """Permission to check if user has Admin role in current tenant."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        return UserRole.objects.filter(
            user=request.user, tenant=tenant, role__name="admin"
        ).exists()


class IsInstructorOrAdmin(permissions.BasePermission):
    """Permission to check if user has Instructor or Admin role."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        return UserRole.objects.filter(
            user=request.user,
            tenant=tenant,
            role__name__in=["admin", "instructor"],
        ).exists()


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to check if user is the object owner or has Admin role."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(obj, "user"):
            is_owner = obj.user.id == request.user.id
        else:
            is_owner = obj.id == request.user.id

        if is_owner:
            return True

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        return UserRole.objects.filter(
            user=request.user, tenant=tenant, role__name="admin"
        ).exists()


class CanManageUsers(permissions.BasePermission):
    """Permission to check if user can manage users (has manage_users permission)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        user_roles = UserRole.objects.filter(
            user=request.user, tenant=tenant
        ).select_related("role")

        for user_role in user_roles:
            if "manage_users" in user_role.role.permissions:
                return True

        return False


class CanManageRoles(permissions.BasePermission):
    """Permission to check if user can manage roles (has manage_roles permission)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        user_roles = UserRole.objects.filter(
            user=request.user, tenant=tenant
        ).select_related("role")

        for user_role in user_roles:
            if "manage_roles" in user_role.role.permissions:
                return True

        return False


class ReadOnly(permissions.BasePermission):
    """Permission that allows only safe methods (GET, HEAD, OPTIONS)."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
