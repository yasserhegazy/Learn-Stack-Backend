"""
Unit tests for User & Role Management models.

Following TDD approach - tests will be written first,
then implementation follows.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from modules.users.models import Role, Tenant, User, UserRole

pytestmark = pytest.mark.django_db


class TestTenantModel:
    def test_create_tenant_with_valid_subdomain(self):
        tenant = Tenant.objects.create(name="Test Organization", subdomain="test-org")

        assert tenant.name == "Test Organization"
        assert tenant.subdomain == "test-org"
        assert tenant.is_active is True
        assert tenant.subscription_plan == "free"
        assert tenant.settings == {}

    def test_subdomain_must_be_unique(self):
        Tenant.objects.create(name="Org 1", subdomain="myorg")

        with pytest.raises(IntegrityError):
            Tenant.objects.create(name="Org 2", subdomain="myorg")

    def test_subdomain_validation_rejects_uppercase(self):
        tenant = Tenant(name="Test", subdomain="TestOrg")

        with pytest.raises(ValidationError):
            tenant.full_clean()

    def test_subdomain_validation_rejects_special_chars(self):
        tenant = Tenant(name="Test", subdomain="test_org")

        with pytest.raises(ValidationError):
            tenant.full_clean()

    def test_tenant_string_representation(self):
        tenant = Tenant.objects.create(name="My Company", subdomain="mycompany")

        assert str(tenant) == "My Company"


class TestUserModel:
    def test_create_user_with_tenant(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="password123",
            tenant=tenant,
        )

        assert user.username == "john"
        assert user.email == "john@example.com"
        assert user.tenant == tenant
        assert user.is_verified is False
        assert user.timezone == "UTC"
        assert user.language == "en"

    def test_username_unique_per_tenant(self):
        tenant1 = Tenant.objects.create(name="Tenant 1", subdomain="tenant1")
        tenant2 = Tenant.objects.create(name="Tenant 2", subdomain="tenant2")

        User.objects.create_user(
            username="john", email="john1@example.com", tenant=tenant1
        )

        user2 = User.objects.create_user(
            username="john", email="john2@example.com", tenant=tenant2
        )

        assert user2.username == "john"

    def test_email_unique_per_tenant(self):
        tenant1 = Tenant.objects.create(name="Tenant 1", subdomain="tenant1")
        tenant2 = Tenant.objects.create(name="Tenant 2", subdomain="tenant2")

        User.objects.create_user(
            username="john1", email="john@example.com", tenant=tenant1
        )

        user2 = User.objects.create_user(
            username="john2", email="john@example.com", tenant=tenant2
        )

        assert user2.email == "john@example.com"

    def test_duplicate_username_in_same_tenant_fails(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        User.objects.create_user(
            username="john", email="john1@example.com", tenant=tenant
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="john", email="john2@example.com", tenant=tenant
            )

    def test_user_string_representation(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant
        )

        assert str(user) == "john (School)"


class TestRoleModel:
    def test_create_role(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        role = Role.objects.create(
            name=Role.ADMIN,
            tenant=tenant,
            description="Administrator role",
            is_system_role=True,
        )

        assert role.name == "admin"
        assert role.tenant == tenant
        assert role.is_system_role is True
        assert role.permissions == []

    def test_role_name_unique_per_tenant(self):
        tenant1 = Tenant.objects.create(name="Tenant 1", subdomain="tenant1")
        tenant2 = Tenant.objects.create(name="Tenant 2", subdomain="tenant2")

        Role.objects.create(name=Role.ADMIN, tenant=tenant1)
        role2 = Role.objects.create(name=Role.ADMIN, tenant=tenant2)

        assert role2.tenant == tenant2

    def test_duplicate_role_name_in_same_tenant_fails(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        Role.objects.create(name=Role.ADMIN, tenant=tenant)

        with pytest.raises(IntegrityError):
            Role.objects.create(name=Role.ADMIN, tenant=tenant)

    def test_role_string_representation(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        role = Role.objects.create(name=Role.INSTRUCTOR, tenant=tenant)

        assert str(role) == "Instructor - School"


class TestUserRoleModel:
    def test_assign_role_to_user(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant
        )
        role = Role.objects.create(name=Role.STUDENT, tenant=tenant)
        admin = User.objects.create_user(
            username="admin", email="admin@example.com", tenant=tenant
        )

        user_role = UserRole.objects.create(
            user=user, role=role, tenant=tenant, assigned_by=admin
        )

        assert user_role.user == user
        assert user_role.role == role
        assert user_role.tenant == tenant
        assert user_role.assigned_by == admin

    def test_user_role_unique_constraint(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant
        )
        role = Role.objects.create(name=Role.STUDENT, tenant=tenant)

        UserRole.objects.create(user=user, role=role, tenant=tenant)

        with pytest.raises(IntegrityError):
            UserRole.objects.create(user=user, role=role, tenant=tenant)

    def test_user_role_validates_tenant_consistency_for_user(self):
        tenant1 = Tenant.objects.create(name="Tenant 1", subdomain="tenant1")
        tenant2 = Tenant.objects.create(name="Tenant 2", subdomain="tenant2")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant1
        )
        role = Role.objects.create(name=Role.STUDENT, tenant=tenant2)

        with pytest.raises(ValueError, match="User must belong to the same tenant"):
            UserRole.objects.create(user=user, role=role, tenant=tenant2)

    def test_user_role_validates_tenant_consistency_for_role(self):
        tenant1 = Tenant.objects.create(name="Tenant 1", subdomain="tenant1")
        tenant2 = Tenant.objects.create(name="Tenant 2", subdomain="tenant2")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant1
        )
        role = Role.objects.create(name=Role.STUDENT, tenant=tenant2)

        with pytest.raises(ValueError, match="Role must belong to the same tenant"):
            UserRole.objects.create(user=user, role=role, tenant=tenant1)

    def test_user_role_validates_tenant_consistency_for_assigner(self):
        tenant1 = Tenant.objects.create(name="Tenant 1", subdomain="tenant1")
        tenant2 = Tenant.objects.create(name="Tenant 2", subdomain="tenant2")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant1
        )
        role = Role.objects.create(name=Role.STUDENT, tenant=tenant1)
        admin = User.objects.create_user(
            username="admin", email="admin@example.com", tenant=tenant2
        )

        with pytest.raises(ValueError, match="Assigner must belong to the same tenant"):
            UserRole.objects.create(
                user=user, role=role, tenant=tenant1, assigned_by=admin
            )

    def test_user_can_have_multiple_roles_in_same_tenant(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant
        )
        student_role = Role.objects.create(name=Role.STUDENT, tenant=tenant)
        instructor_role = Role.objects.create(name=Role.INSTRUCTOR, tenant=tenant)

        UserRole.objects.create(user=user, role=student_role, tenant=tenant)
        UserRole.objects.create(user=user, role=instructor_role, tenant=tenant)

        assert user.user_roles.count() == 2

    def test_user_role_string_representation(self):
        tenant = Tenant.objects.create(name="School", subdomain="school")
        user = User.objects.create_user(
            username="john", email="john@example.com", tenant=tenant
        )
        role = Role.objects.create(name=Role.STUDENT, tenant=tenant)
        user_role = UserRole.objects.create(user=user, role=role, tenant=tenant)

        assert str(user_role) == "john - student (School)"


# Model tests will be defined here following TDD approach
