"""
Serializers for User & Role Management Module

DTOs for API input validation and output formatting.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from modules.users.models import Role, Tenant, User, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes tenant_id in token claims."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["tenant_id"] = user.tenant_id
        token["tenant_subdomain"] = user.tenant.subdomain
        token["username"] = user.username
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "tenant_id": self.user.tenant_id,
            "tenant_name": self.user.tenant.name,
        }
        return data


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "subdomain",
            "is_active",
            "subscription_plan",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model with tenant context."""

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "is_system_role",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "is_system_role"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and hasattr(request, "tenant"):
            if self.instance and self.instance.tenant != request.tenant:
                raise serializers.ValidationError(
                    "Cannot modify role from another tenant"
                )
            attrs["tenant"] = request.tenant
        return attrs


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole assignments with tenant validation."""

    role_name = serializers.CharField(source="role.get_name_display", read_only=True)
    assigned_by_username = serializers.CharField(
        source="assigned_by.username", read_only=True, allow_null=True
    )

    class Meta:
        model = UserRole
        fields = [
            "id",
            "user",
            "role",
            "role_name",
            "assigned_by",
            "assigned_by_username",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "assigned_by"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = attrs.get("user")
        role = attrs.get("role")

        if request and hasattr(request, "tenant"):
            if user.tenant != request.tenant:
                raise serializers.ValidationError(
                    {"user": "User must belong to current tenant"}
                )
            if role.tenant != request.tenant:
                raise serializers.ValidationError(
                    {"role": "Role must belong to current tenant"}
                )
            attrs["tenant"] = request.tenant
            if request.user.is_authenticated:
                attrs["assigned_by"] = request.user
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Minimal user serializer for list views."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "tenant_name",
            "roles",
            "is_active",
            "is_verified",
            "date_joined",
        ]

    def get_roles(self, obj):
        return [ur.role.name for ur in obj.user_roles.all()]


class UserProfileSerializer(serializers.ModelSerializer):
    """Public user profile serializer (limited fields)."""

    tenant = TenantSerializer(read_only=True)
    user_roles = UserRoleSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "tenant",
            "user_roles",
            "date_joined",
        ]


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer with write capabilities."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    roles = UserRoleSerializer(source="user_roles", many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "bio",
            "tenant",
            "tenant_name",
            "roles",
            "is_active",
            "is_verified",
            "is_staff",
            "timezone",
            "language",
            "last_login",
            "date_joined",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "is_verified",
            "is_staff",
            "last_login",
            "date_joined",
            "created_at",
        ]

    def validate_email(self, value):
        request = self.context.get("request")
        if request and hasattr(request, "tenant"):
            query = User.objects.filter(email=value, tenant=request.tenant)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError(
                    "A user with this email already exists in your organization"
                )
        return value

    def validate_username(self, value):
        request = self.context.get("request")
        if request and hasattr(request, "tenant"):
            query = User.objects.filter(username=value, tenant=request.tenant)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError(
                    "A user with this username already exists in your organization"
                )
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if self.instance and request and hasattr(request, "tenant"):
            if self.instance.tenant_id != request.tenant.id:
                raise serializers.ValidationError(
                    "User must belong to the current tenant"
                )
        return attrs


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user creation/registration with password handling."""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_number",
            "timezone",
            "language",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match"}
            )
        attrs.pop("password_confirm")

        request = self.context.get("request")
        if request and hasattr(request, "tenant"):
            if User.objects.filter(
                email=attrs["email"], tenant=request.tenant
            ).exists():
                raise serializers.ValidationError(
                    {"email": "A user with this email already exists"}
                )
            if User.objects.filter(
                username=attrs["username"], tenant=request.tenant
            ).exists():
                raise serializers.ValidationError(
                    {"username": "A user with this username already exists"}
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant"):
            validated_data["tenant"] = request.tenant

        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match"}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
