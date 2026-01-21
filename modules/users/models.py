"""
Models for User & Role Management Module

Defines User, Role, and Profile models with multi-tenant support.
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimestampedModel):
    name = models.CharField(max_length=255)
    subdomain = models.SlugField(
        max_length=63,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$",
                message=_("Subdomain must be lowercase alphanumeric with hyphens"),
            )
        ],
    )
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    subscription_plan = models.CharField(
        max_length=50,
        choices=[
            ("free", "Free"),
            ("basic", "Basic"),
            ("professional", "Professional"),
            ("enterprise", "Enterprise"),
        ],
        default="free",
    )

    class Meta:
        db_table = "tenants"
        indexes = [
            models.Index(fields=["subdomain"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class User(AbstractUser, TimestampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(max_length=500, blank=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["tenant", "email"]),
            models.Index(fields=["tenant", "is_active"]),
        ]
        unique_together = [["tenant", "username"], ["tenant", "email"]]

    def __str__(self):
        return f"{self.username} ({self.tenant.name})"


class Role(TimestampedModel):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (INSTRUCTOR, "Instructor"),
        (STUDENT, "Student"),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="roles")
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, blank=True)
    is_system_role = models.BooleanField(default=True)

    class Meta:
        db_table = "roles"
        unique_together = [["tenant", "name"]]
        indexes = [
            models.Index(fields=["tenant", "name"]),
        ]

    def __str__(self):
        return f"{self.get_name_display()} - {self.tenant.name}"


class UserRole(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="user_roles"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="role_assignments_made",
    )

    class Meta:
        db_table = "user_roles"
        unique_together = [["user", "role", "tenant"]]
        indexes = [
            models.Index(fields=["user", "tenant"]),
            models.Index(fields=["role", "tenant"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role.name} ({self.tenant.name})"

    def save(self, *args, **kwargs):
        self._validate_tenant_consistency()
        super().save(*args, **kwargs)

    def _validate_tenant_consistency(self):
        if self.user.tenant_id != self.tenant_id:
            raise ValueError("User must belong to the same tenant")
        if self.role.tenant_id != self.tenant_id:
            raise ValueError("Role must belong to the same tenant")
        if self.assigned_by and self.assigned_by.tenant_id != self.tenant_id:
            raise ValueError("Assigner must belong to the same tenant")
