"""
Unit tests for User & Role Management permissions.
"""

import pytest
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from modules.users.factories import RoleFactory, TenantFactory, UserFactory
from modules.users.models import Role, UserRole
from modules.users.permissions import (
    CanManageRoles,
    CanManageUsers,
    IsAdminRole,
    IsInstructorOrAdmin,
    IsOwnerOrAdmin,
    IsTenantMember,
    ReadOnly,
)


@pytest.mark.django_db
class TestIsTenantMember(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant1 = TenantFactory(subdomain="tenant1")
        self.tenant2 = TenantFactory(subdomain="tenant2")
        self.user1 = UserFactory(tenant=self.tenant1)
        self.permission = IsTenantMember()

    def test_user_belongs_to_tenant(self):
        request = self.factory.get("/")
        request.user = self.user1
        request.tenant = self.tenant1
        # Ensure user.tenant is properly set
        self.user1.tenant = self.tenant1
        self.user1.save()

    def test_user_does_not_belong_to_tenant(self):
        request = self.factory.get("/")
        request.user = self.user1
        request.tenant = self.tenant2
        request_obj = Request(request)

        assert self.permission.has_permission(request_obj, None) is False

    def test_unauthenticated_user(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.tenant = self.tenant1
        request_obj = Request(request)

        assert self.permission.has_permission(request_obj, None) is False


@pytest.mark.django_db
class TestIsAdminRole(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.admin_user = UserFactory(tenant=self.tenant)
        self.regular_user = UserFactory(tenant=self.tenant)

        self.admin_role = RoleFactory(tenant=self.tenant, name=Role.ADMIN)
        UserRole.objects.create(
            user=self.admin_user, role=self.admin_role, tenant=self.tenant
        )

        self.permission = IsAdminRole()

    def test_user_has_admin_role(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        request.tenant = self.tenant
        request_obj = Request(request)
        request_obj.tenant = self.tenant
        request_obj._user = self.admin_user

        assert self.permission.has_permission(request_obj, None) is True

    def test_user_does_not_have_admin_role(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        request.tenant = self.tenant
        request_obj = Request(request)

        assert self.permission.has_permission(request_obj, None) is False


@pytest.mark.django_db
class TestIsInstructorOrAdmin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.admin_user = UserFactory(tenant=self.tenant)
        self.instructor_user = UserFactory(tenant=self.tenant)
        self.student_user = UserFactory(tenant=self.tenant)

        self.admin_role = RoleFactory(tenant=self.tenant, name=Role.ADMIN)
        self.instructor_role = RoleFactory(tenant=self.tenant, name=Role.INSTRUCTOR)

        UserRole.objects.create(
            user=self.admin_user, role=self.admin_role, tenant=self.tenant
        )
        UserRole.objects.create(
            user=self.instructor_user, role=self.instructor_role, tenant=self.tenant
        )

        self.permission = IsInstructorOrAdmin()

    def test_admin_has_permission(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        request.tenant = self.tenant
        request_obj = Request(request)
        request_obj.tenant = self.tenant
        request_obj._user = self.admin_user

        assert self.permission.has_permission(request_obj, None) is True

    def test_instructor_has_permission(self):
        request = self.factory.get("/")
        request.user = self.instructor_user
        request.tenant = self.tenant
        request_obj = Request(request)
        request_obj.tenant = self.tenant
        request_obj._user = self.instructor_user

        assert self.permission.has_permission(request_obj, None) is True

    def test_student_does_not_have_permission(self):
        request = self.factory.get("/")
        request.user = self.student_user
        request.tenant = self.tenant
        request_obj = Request(request)

        assert self.permission.has_permission(request_obj, None) is False


@pytest.mark.django_db
class TestIsOwnerOrAdmin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.owner_user = UserFactory(tenant=self.tenant)
        self.admin_user = UserFactory(tenant=self.tenant)
        self.other_user = UserFactory(tenant=self.tenant)

        self.admin_role = RoleFactory(tenant=self.tenant, name=Role.ADMIN)
        UserRole.objects.create(
            user=self.admin_user, role=self.admin_role, tenant=self.tenant
        )

        self.permission = IsOwnerOrAdmin()

    def test_owner_has_permission(self):
        request = self.factory.get("/")
        request.user = self.owner_user
        request.tenant = self.tenant
        request_obj = Request(request)
        request_obj.tenant = self.tenant
        request_obj._user = self.owner_user

        assert (
            self.permission.has_object_permission(request_obj, None, self.owner_user)
            is True
        )

    def test_admin_has_permission_on_other_object(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        request.tenant = self.tenant
        request_obj = Request(request)
        request_obj.tenant = self.tenant
        request_obj._user = self.admin_user

        assert (
            self.permission.has_object_permission(request_obj, None, self.owner_user)
            is True
        )

    def test_other_user_does_not_have_permission(self):
        request = self.factory.get("/")
        request.user = self.other_user
        request.tenant = self.tenant
        request_obj = Request(request)

        assert (
            self.permission.has_object_permission(request_obj, None, self.owner_user)
            is False
        )


@pytest.mark.django_db
class TestCanManageUsers(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.admin_user = UserFactory(tenant=self.tenant)
        self.regular_user = UserFactory(tenant=self.tenant)

        self.admin_role = RoleFactory(
            tenant=self.tenant,
            name=Role.ADMIN,
            permissions=["manage_users", "manage_roles"],
        )
        UserRole.objects.create(
            user=self.admin_user, role=self.admin_role, tenant=self.tenant
        )

        self.permission = CanManageUsers()

    def test_user_with_manage_users_permission(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        request.tenant = self.tenant
        request_obj = Request(request)
        request_obj.tenant = self.tenant
        request_obj._user = self.admin_user

        assert self.permission.has_permission(request_obj, None) is True

    def test_user_without_manage_users_permission(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        request.tenant = self.tenant
        request_obj = Request(request)

        assert self.permission.has_permission(request_obj, None) is False


@pytest.mark.django_db
class TestCanManageRoles(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.admin_user = UserFactory(tenant=self.tenant)
        self.regular_user = UserFactory(tenant=self.tenant)

        self.admin_role = RoleFactory(
            tenant=self.tenant,
            name=Role.ADMIN,
            permissions=["manage_roles", "manage_users"],
        )
        UserRole.objects.create(
            user=self.admin_user, role=self.admin_role, tenant=self.tenant
        )

        self.permission = CanManageRoles()

    def test_user_with_manage_roles_permission(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        request.tenant = self.tenant
        request_obj = Request(request)
        request_obj.tenant = self.tenant
        request_obj._user = self.admin_user

        assert self.permission.has_permission(request_obj, None) is True

    def test_user_without_manage_roles_permission(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        request.tenant = self.tenant
        request_obj = Request(request)

        assert self.permission.has_permission(request_obj, None) is False


@pytest.mark.django_db
class TestReadOnly(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = ReadOnly()

    def test_safe_methods_allowed(self):
        for method in ["GET", "HEAD", "OPTIONS"]:
            request = getattr(self.factory, method.lower())("/")
            request_obj = Request(request)
            assert self.permission.has_permission(request_obj, None) is True

    def test_unsafe_methods_denied(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            request = getattr(self.factory, method.lower())("/")
            request_obj = Request(request)
            assert self.permission.has_permission(request_obj, None) is False
