"""
Unit tests for User & Role Management serializers.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from modules.users.factories import RoleFactory, TenantFactory, UserFactory
from modules.users.models import Role, UserRole
from modules.users.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    RoleSerializer,
    TenantSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserRoleSerializer,
    UserSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestTenantSerializer(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()

    def test_serialize_tenant(self):
        serializer = TenantSerializer(self.tenant)
        data = serializer.data

        assert data["id"] == self.tenant.id
        assert data["name"] == self.tenant.name
        assert data["subdomain"] == self.tenant.subdomain
        assert data["subscription_plan"] == self.tenant.subscription_plan
        assert data["is_active"] == self.tenant.is_active

    def test_create_tenant(self):
        data = {
            "name": "Test Company",
            "subdomain": "uniquetestco",
            "subscription_plan": "professional",
        }
        serializer = TenantSerializer(data=data)
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
        assert serializer.is_valid()
        tenant = serializer.save()

        assert tenant.name == "Test Company"
        assert tenant.subdomain == "uniquetestco"
        data = {
            "name": "Test Company",
            "subdomain": "Test-Co",  # Invalid: uppercase and hyphen
        }
        serializer = TenantSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestRoleSerializer(TestCase):
    def setUp(self):
        self.tenant = TenantFactory()
        self.role = RoleFactory(tenant=self.tenant, name=Role.ADMIN)

    def test_serialize_role(self):
        serializer = RoleSerializer(self.role)
        data = serializer.data

        assert data["id"] == self.role.id
        assert data["name"] == self.role.name
        assert data["description"] == self.role.description
        assert data["permissions"] == self.role.permissions


@pytest.mark.django_db
class TestUserSerializer(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)

    def test_serialize_user(self):
        request = self.factory.get("/")
        request.tenant = self.tenant
        request_obj = Request(request)

        serializer = UserSerializer(self.user, context={"request": request_obj})
        data = serializer.data

        assert data["id"] == self.user.id
        assert data["username"] == self.user.username
        assert data["email"] == self.user.email
        assert "password" not in data

    def test_tenant_validation_mismatch(self):
        tenant2 = TenantFactory(subdomain="tenant2")
        user2 = UserFactory(tenant=tenant2)

        request = self.factory.get("/")
        request.tenant = self.tenant
        request_obj = Request(request)

        data = {"username": "newuser", "email": "new@example.com"}
        serializer = UserSerializer(
            user2, data=data, context={"request": request_obj}, partial=True
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "must belong to the current tenant" in str(exc_info.value)


@pytest.mark.django_db
class TestUserCreateSerializer(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()

    def test_create_user_with_password_confirmation(self):
        request = self.factory.post("/")
        request.tenant = self.tenant
        request_obj = Request(request)

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "New",
            "last_name": "User",
        }

        serializer = UserCreateSerializer(data=data, context={"request": request_obj})
        assert serializer.is_valid()
        user = serializer.save()

        assert user.username == "newuser"
        assert user.tenant == self.tenant
        assert user.check_password("securepass123")

    def test_password_mismatch(self):
        request = self.factory.post("/")
        request.tenant = self.tenant
        request_obj = Request(request)

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "password_confirm": "differentpass",
        }

        serializer = UserCreateSerializer(data=data, context={"request": request_obj})
        assert not serializer.is_valid()
        assert "Passwords do not match" in str(serializer.errors)


@pytest.mark.django_db
class TestUserListSerializer(TestCase):
    def setUp(self):
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)
        self.role = RoleFactory(tenant=self.tenant, name=Role.STUDENT)
        UserRole.objects.create(user=self.user, role=self.role, tenant=self.tenant)

    def test_serialize_user_list(self):
        serializer = UserListSerializer(self.user)
        data = serializer.data

        assert data["id"] == self.user.id
        assert data["username"] == self.user.username
        assert data["email"] == self.user.email
        assert len(data["roles"]) == 1
        assert data["roles"][0] == Role.STUDENT


@pytest.mark.django_db
class TestUserProfileSerializer(TestCase):
    def setUp(self):
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)
        self.role = RoleFactory(tenant=self.tenant, name=Role.INSTRUCTOR)
        UserRole.objects.create(user=self.user, role=self.role, tenant=self.tenant)

    def test_serialize_user_profile(self):
        serializer = UserProfileSerializer(self.user)
        data = serializer.data

        assert data["id"] == self.user.id
        assert data["username"] == self.user.username
        assert data["tenant"]["id"] == self.tenant.id
        assert len(data["user_roles"]) == 1


@pytest.mark.django_db
class TestUserRoleSerializer(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)
        self.role = RoleFactory(tenant=self.tenant)
        self.user_role = UserRole.objects.create(
            user=self.user, role=self.role, tenant=self.tenant
        )

    def test_serialize_user_role(self):
        request = self.factory.get("/")
        request.tenant = self.tenant
        request_obj = Request(request)

        serializer = UserRoleSerializer(
            self.user_role, context={"request": request_obj}
        )
        data = serializer.data

        assert data["user"] == self.user.id
        assert data["role"] == self.role.id


@pytest.mark.django_db
class TestPasswordChangeSerializer(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)
        self.user.set_password("oldpass123")
        self.user.save()

    def test_change_password_success(self):
        request = self.factory.post("/")
        request.user = self.user
        request_obj = Request(request)
        # Force the user on the DRF Request object
        request_obj._user = self.user

        data = {
            "old_password": "oldpass123",
            "new_password": "newpass456",
            "new_password_confirm": "newpass456",
        }

        serializer = PasswordChangeSerializer(
            data=data, context={"request": request_obj}
        )
        assert serializer.is_valid()
        serializer.save()

        self.user.refresh_from_db()
        assert self.user.check_password("newpass456")

    def test_wrong_old_password(self):
        request = self.factory.post("/")
        request.user = self.user
        request_obj = Request(request)
        request_obj._user = self.user

        data = {
            "old_password": "wrongpass",
            "new_password": "newpass456",
            "new_password_confirm": "newpass456",
        }

        serializer = PasswordChangeSerializer(
            data=data, context={"request": request_obj}
        )
        assert not serializer.is_valid()
        assert "Old password is incorrect" in str(serializer.errors)

    def test_new_password_mismatch(self):
        request = self.factory.post("/")
        request.user = self.user
        request_obj = Request(request)
        request_obj._user = self.user

        data = {
            "old_password": "oldpass123",
            "new_password": "newpass456",
            "new_password_confirm": "different",
        }

        serializer = PasswordChangeSerializer(
            data=data, context={"request": request_obj}
        )
        assert not serializer.is_valid()
        assert "New passwords do not match" in str(serializer.errors)


@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer(TestCase):
    def setUp(self):
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant, username="testuser")
        self.user.set_password("testpass123")
        self.user.save()

    def test_token_contains_tenant_claims(self):
        data = {"username": "testuser", "password": "testpass123"}
        serializer = CustomTokenObtainPairSerializer(data=data)

        assert serializer.is_valid()
        token_data = serializer.validated_data

        # Decode the access token to check claims
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken(token_data["access"])

        assert token["tenant_id"] == self.tenant.id
        assert token["tenant_subdomain"] == self.tenant.subdomain
        assert token["username"] == "testuser"
        assert token["email"] == self.user.email
