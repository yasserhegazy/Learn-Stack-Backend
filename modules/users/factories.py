"""
Test Factories for User & Role Management Module

Factory Boy factories for generating test data.
"""

import factory
from django.contrib.auth.hashers import make_password
from factory.django import DjangoModelFactory
from faker import Faker

from modules.users.models import Role, Tenant, User, UserRole

fake = Faker()


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant
        django_get_or_create = ("subdomain",)

    name = factory.Faker("company")
    subdomain = factory.Sequence(lambda n: f"tenant{n}")
    is_active = True
    subscription_plan = "free"
    settings = factory.Dict({})


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username", "tenant")

    tenant = factory.SubFactory(TenantFactory)
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.LazyFunction(lambda: make_password("password123"))
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    is_verified = False
    timezone = "UTC"
    language = "en"


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ("name", "tenant")

    tenant = factory.SubFactory(TenantFactory)
    name = Role.STUDENT
    description = factory.LazyAttribute(
        lambda obj: f"{obj.get_name_display()} role description"
    )
    permissions = factory.List([])
    is_system_role = True


class UserRoleFactory(DjangoModelFactory):
    class Meta:
        model = UserRole

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(
        RoleFactory, tenant=factory.SelfAttribute("..user.tenant")
    )
    tenant = factory.SelfAttribute("user.tenant")
    assigned_by = None
