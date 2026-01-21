"""
Services for User & Role Management Module

Business logic and providers (tenant-aware).
"""

from django.db import transaction

from modules.users.models import Role, Tenant, User, UserRole


class UserService:
    """Service class for user-related business logic."""

    @staticmethod
    @transaction.atomic
    def create_user(user_data, tenant, assign_default_role=True):
        """Create a new user with optional default role assignment."""
        user_data["tenant"] = tenant
        password = user_data.pop("password", None)

        user = User.objects.create(**user_data)
        if password:
            user.set_password(password)
            user.save()

        if assign_default_role:
            student_role = Role.objects.filter(tenant=tenant, name=Role.STUDENT).first()
            if student_role:
                UserRole.objects.create(user=user, role=student_role, tenant=tenant)

        return user

    @staticmethod
    def update_user(user, update_data, requesting_user=None):
        """Update user information with permission checks."""
        update_data.pop("tenant", None)
        update_data.pop("tenant_id", None)
        update_data.pop("password", None)

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        user.save()
        return user

    @staticmethod
    def deactivate_user(user):
        """Deactivate a user (soft delete)."""
        user.is_active = False
        user.save()
        return user

    @staticmethod
    def activate_user(user):
        """Activate a previously deactivated user."""
        user.is_active = True
        user.save()
        return user

    @staticmethod
    def change_password(user, old_password, new_password):
        """Change user's password with old password verification."""
        if not user.check_password(old_password):
            raise ValueError("Old password is incorrect")

        user.set_password(new_password)
        user.save()
        return True

    @staticmethod
    def get_users_by_tenant(tenant, filters=None):
        """Get all users for a tenant with optional filters."""
        queryset = User.objects.filter(tenant=tenant).select_related("tenant")
        if filters:
            queryset = queryset.filter(**filters)
        return queryset


class RoleService:
    """Service class for role-related business logic."""

    @staticmethod
    @transaction.atomic
    def assign_role(user, role, tenant, assigned_by=None):
        """Assign a role to a user with tenant validation."""
        if user.tenant != tenant:
            raise ValueError("User must belong to the same tenant")
        if role.tenant != tenant:
            raise ValueError("Role must belong to the same tenant")
        if assigned_by and assigned_by.tenant != tenant:
            raise ValueError("Assigner must belong to the same tenant")

        existing = UserRole.objects.filter(user=user, role=role, tenant=tenant).first()
        if existing:
            return existing

        user_role = UserRole.objects.create(
            user=user, role=role, tenant=tenant, assigned_by=assigned_by
        )
        return user_role

    @staticmethod
    def remove_role(user, role, tenant):
        """Remove a role from a user."""
        deleted, _ = UserRole.objects.filter(
            user=user, role=role, tenant=tenant
        ).delete()
        return deleted

    @staticmethod
    def get_user_roles(user, tenant):
        """Get all roles assigned to a user in a tenant."""
        return UserRole.objects.filter(user=user, tenant=tenant).select_related(
            "role", "assigned_by"
        )

    @staticmethod
    def get_users_with_role(role, tenant):
        """Get all users with a specific role in a tenant."""
        user_ids = UserRole.objects.filter(role=role, tenant=tenant).values_list(
            "user_id", flat=True
        )
        return User.objects.filter(id__in=user_ids, tenant=tenant)

    @staticmethod
    def has_permission(user, permission_name, tenant):
        """Check if user has a specific permission in tenant."""
        user_roles = UserRole.objects.filter(user=user, tenant=tenant).select_related(
            "role"
        )

        for user_role in user_roles:
            if permission_name in user_role.role.permissions:
                return True
        return False


class TenantService:
    """Service class for tenant-related business logic."""

    @staticmethod
    @transaction.atomic
    def create_tenant_with_admin(tenant_data, admin_user_data):
        """Create a new tenant with an admin user and default roles."""
        tenant = Tenant.objects.create(**tenant_data)
        roles_created = TenantService._create_default_roles(tenant)

        admin_user_data["tenant"] = tenant
        admin_user_data["is_staff"] = True
        password = admin_user_data.pop("password", None)

        admin_user = User.objects.create(**admin_user_data)
        if password:
            admin_user.set_password(password)
            admin_user.save()

        admin_role = roles_created.get("admin")
        if admin_role:
            UserRole.objects.create(user=admin_user, role=admin_role, tenant=tenant)

        return tenant, admin_user

    @staticmethod
    def _create_default_roles(tenant):
        """Create default roles for a tenant."""
        default_roles = {
            "admin": {
                "name": Role.ADMIN,
                "description": "Full access to tenant resources",
                "permissions": [
                    "manage_users",
                    "manage_roles",
                    "manage_courses",
                    "manage_assessments",
                    "view_analytics",
                    "manage_settings",
                ],
            },
            "instructor": {
                "name": Role.INSTRUCTOR,
                "description": "Create and manage courses",
                "permissions": [
                    "create_courses",
                    "manage_own_courses",
                    "create_assessments",
                    "grade_submissions",
                    "view_student_progress",
                    "issue_certificates",
                ],
            },
            "student": {
                "name": Role.STUDENT,
                "description": "Enroll in courses",
                "permissions": [
                    "enroll_courses",
                    "view_courses",
                    "submit_assessments",
                    "view_own_progress",
                    "view_certificates",
                ],
            },
        }

        created_roles = {}
        for role_key, role_data in default_roles.items():
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                tenant=tenant,
                defaults={
                    "description": role_data["description"],
                    "permissions": role_data["permissions"],
                    "is_system_role": True,
                },
            )
            created_roles[role_key] = role

        return created_roles

    @staticmethod
    def update_tenant_settings(tenant, settings_data):
        """Update tenant settings."""
        current_settings = tenant.settings or {}
        current_settings.update(settings_data)
        tenant.settings = current_settings
        tenant.save()
        return tenant
