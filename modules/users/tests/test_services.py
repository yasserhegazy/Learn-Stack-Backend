"""
Unit tests for User & Role Management services.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from modules.users.factories import RoleFactory, TenantFactory, UserFactory
from modules.users.models import Role, User, UserRole
from modules.users.services import RoleService, TenantService, UserService


@pytest.mark.django_db
class TestUserService(TestCase):
    def setUp(self):
        self.tenant = TenantFactory()
        self.student_role = RoleFactory(tenant=self.tenant, name=Role.STUDENT)

    def test_create_user_with_default_role(self):
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "User",
        }

        user = UserService.create_user(user_data, self.tenant, assign_default_role=True)

        assert user.username == "newuser"
        assert user.tenant == self.tenant
        assert user.check_password("securepass123")

        # Check default role assigned
        user_role = UserRole.objects.filter(user=user, tenant=self.tenant).first()
        assert user_role is not None
        assert user_role.role.name == Role.STUDENT

    def test_create_user_without_default_role(self):
        user_data = {
            "username": "newuser2",
            "email": "newuser2@example.com",
            "password": "securepass123",
        }

        user = UserService.create_user(
            user_data, self.tenant, assign_default_role=False
        )

        assert user.username == "newuser2"
        assert user.tenant == self.tenant

        # Check no role assigned
        user_role_count = UserRole.objects.filter(user=user, tenant=self.tenant).count()
        assert user_role_count == 0

    def test_update_user(self):
        user = UserFactory(tenant=self.tenant, first_name="Old")

        update_data = {"first_name": "New", "last_name": "Updated"}
        updated_user = UserService.update_user(user, update_data)

        assert updated_user.first_name == "New"
        assert updated_user.last_name == "Updated"

    def test_update_user_cannot_change_tenant(self):
        user = UserFactory(tenant=self.tenant)
        tenant2 = TenantFactory(subdomain="tenant2")

        update_data = {"tenant": tenant2, "first_name": "Changed"}
        updated_user = UserService.update_user(user, update_data)

        # Tenant should not change
        assert updated_user.tenant == self.tenant
        # But other fields should update
        assert updated_user.first_name == "Changed"

    def test_deactivate_user(self):
        user = UserFactory(tenant=self.tenant, is_active=True)

        UserService.deactivate_user(user)

        user.refresh_from_db()
        assert user.is_active is False

    def test_activate_user(self):
        user = UserFactory(tenant=self.tenant, is_active=False)

        UserService.activate_user(user)

        user.refresh_from_db()
        assert user.is_active is True

    def test_change_password_success(self):
        user = UserFactory(tenant=self.tenant)
        user.set_password("oldpass123")
        user.save()

        result = UserService.change_password(user, "oldpass123", "newpass456")

        assert result is True
        user.refresh_from_db()
        assert user.check_password("newpass456")

    def test_change_password_wrong_old_password(self):
        user = UserFactory(tenant=self.tenant)
        user.set_password("oldpass123")
        user.save()

        with pytest.raises(ValueError) as exc_info:
            UserService.change_password(user, "wrongpass", "newpass456")

        assert "Old password is incorrect" in str(exc_info.value)

    def test_get_users_by_tenant(self):
        user1 = UserFactory(tenant=self.tenant)
        user2 = UserFactory(tenant=self.tenant)
        tenant2 = TenantFactory(subdomain="tenant2")
        user3 = UserFactory(tenant=tenant2)

        users = UserService.get_users_by_tenant(self.tenant)

        assert users.count() == 2
        assert user1 in users
        assert user2 in users
        assert user3 not in users

    def test_get_users_by_tenant_with_filters(self):
        user1 = UserFactory(tenant=self.tenant, is_active=True)
        user2 = UserFactory(tenant=self.tenant, is_active=False)

        active_users = UserService.get_users_by_tenant(
            self.tenant, filters={"is_active": True}
        )

        assert active_users.count() == 1
        assert user1 in active_users
        assert user2 not in active_users


@pytest.mark.django_db
class TestRoleService(TestCase):
    def setUp(self):
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)
        self.role = RoleFactory(tenant=self.tenant, name=Role.INSTRUCTOR)
        self.admin_user = UserFactory(tenant=self.tenant)

    def test_assign_role(self):
        user_role = RoleService.assign_role(
            self.user, self.role, self.tenant, self.admin_user
        )

        assert user_role.user == self.user
        assert user_role.role == self.role
        assert user_role.tenant == self.tenant
        assert user_role.assigned_by == self.admin_user

    def test_assign_role_prevents_duplicates(self):
        # Assign role first time
        user_role1 = RoleService.assign_role(self.user, self.role, self.tenant)

        # Assign same role again
        user_role2 = RoleService.assign_role(self.user, self.role, self.tenant)

        # Should return existing assignment
        assert user_role1.id == user_role2.id
        assert UserRole.objects.filter(user=self.user, role=self.role).count() == 1

    def test_assign_role_validates_user_tenant(self):
        tenant2 = TenantFactory(subdomain="tenant2")
        user2 = UserFactory(tenant=tenant2)

        with pytest.raises(ValueError) as exc_info:
            RoleService.assign_role(user2, self.role, self.tenant)

        assert "User must belong to the same tenant" in str(exc_info.value)

    def test_assign_role_validates_role_tenant(self):
        tenant2 = TenantFactory(subdomain="tenant2")
        role2 = RoleFactory(tenant=tenant2)

        with pytest.raises(ValueError) as exc_info:
            RoleService.assign_role(self.user, role2, self.tenant)

        assert "Role must belong to the same tenant" in str(exc_info.value)

    def test_assign_role_validates_assigner_tenant(self):
        tenant2 = TenantFactory(subdomain="tenant2")
        assigner2 = UserFactory(tenant=tenant2)

        with pytest.raises(ValueError) as exc_info:
            RoleService.assign_role(self.user, self.role, self.tenant, assigner2)

        assert "Assigner must belong to the same tenant" in str(exc_info.value)

    def test_remove_role(self):
        UserRole.objects.create(user=self.user, role=self.role, tenant=self.tenant)

        deleted = RoleService.remove_role(self.user, self.role, self.tenant)

        assert deleted == 1
        assert not UserRole.objects.filter(
            user=self.user, role=self.role, tenant=self.tenant
        ).exists()

    def test_remove_nonexistent_role(self):
        deleted = RoleService.remove_role(self.user, self.role, self.tenant)

        assert deleted == 0

    def test_get_user_roles(self):
        role2 = RoleFactory(tenant=self.tenant, name=Role.STUDENT)
        UserRole.objects.create(user=self.user, role=self.role, tenant=self.tenant)
        UserRole.objects.create(user=self.user, role=role2, tenant=self.tenant)

        user_roles = RoleService.get_user_roles(self.user, self.tenant)

        assert user_roles.count() == 2

    def test_get_users_with_role(self):
        user2 = UserFactory(tenant=self.tenant)
        UserRole.objects.create(user=self.user, role=self.role, tenant=self.tenant)
        UserRole.objects.create(user=user2, role=self.role, tenant=self.tenant)

        users = RoleService.get_users_with_role(self.role, self.tenant)

        assert users.count() == 2
        assert self.user in users
        assert user2 in users

    def test_has_permission_true(self):
        role_with_permission = RoleFactory(
            tenant=self.tenant,
            name=Role.ADMIN,
            permissions=["manage_users", "manage_courses"],
        )
        UserRole.objects.create(
            user=self.user, role=role_with_permission, tenant=self.tenant
        )

        has_perm = RoleService.has_permission(self.user, "manage_users", self.tenant)

        assert has_perm is True

    def test_has_permission_false(self):
        role_without_permission = RoleFactory(
            tenant=self.tenant, name=Role.STUDENT, permissions=["view_courses"]
        )
        UserRole.objects.create(
            user=self.user, role=role_without_permission, tenant=self.tenant
        )

        has_perm = RoleService.has_permission(self.user, "manage_users", self.tenant)

        assert has_perm is False


@pytest.mark.django_db
class TestTenantService(TestCase):
    def test_create_tenant_with_admin(self):
        tenant_data = {
            "name": "Test Company",
            "subdomain": "testco",
            "subscription_plan": "premium",
        }

        admin_user_data = {
            "username": "admin",
            "email": "admin@testco.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User",
        }

        tenant, admin_user = TenantService.create_tenant_with_admin(
            tenant_data, admin_user_data
        )

        # Verify tenant created
        assert tenant.name == "Test Company"
        assert tenant.subdomain == "testco"

        # Verify admin user created
        assert admin_user.username == "admin"
        assert admin_user.tenant == tenant
        assert admin_user.is_staff is True
        assert admin_user.check_password("adminpass123")

        # Verify admin role assigned
        admin_role = Role.objects.get(tenant=tenant, name=Role.ADMIN)
        user_role = UserRole.objects.get(user=admin_user, role=admin_role)
        assert user_role is not None

    def test_create_default_roles(self):
        tenant = TenantFactory()

        roles = TenantService._create_default_roles(tenant)

        assert "admin" in roles
        assert "instructor" in roles
        assert "student" in roles

        # Verify roles in database
        admin_role = Role.objects.get(tenant=tenant, name=Role.ADMIN)
        instructor_role = Role.objects.get(tenant=tenant, name=Role.INSTRUCTOR)
        student_role = Role.objects.get(tenant=tenant, name=Role.STUDENT)

        assert admin_role.is_system_role is True
        assert "manage_users" in admin_role.permissions
        assert "create_courses" in instructor_role.permissions
        assert "enroll_courses" in student_role.permissions

    def test_create_default_roles_idempotent(self):
        tenant = TenantFactory()

        # Create roles first time
        roles1 = TenantService._create_default_roles(tenant)

        # Create again - should not duplicate
        roles2 = TenantService._create_default_roles(tenant)

        # Should return same roles
        assert roles1["admin"].id == roles2["admin"].id

        # Should only have 3 roles total
        assert Role.objects.filter(tenant=tenant).count() == 3

    def test_update_tenant_settings(self):
        tenant = TenantFactory(settings={})

        new_settings = {"theme": "dark", "language": "en"}
        updated_tenant = TenantService.update_tenant_settings(tenant, new_settings)

        assert updated_tenant.settings["theme"] == "dark"
        assert updated_tenant.settings["language"] == "en"

    def test_update_tenant_settings_merges(self):
        tenant = TenantFactory(settings={"existing": "value"})

        new_settings = {"theme": "dark"}
        updated_tenant = TenantService.update_tenant_settings(tenant, new_settings)

        assert updated_tenant.settings["existing"] == "value"
        assert updated_tenant.settings["theme"] == "dark"
