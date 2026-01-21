"""
Views for User & Role Management Module

API endpoints (ViewSets/APIViews) acting as controllers.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from modules.users.models import Role, Tenant, User
from modules.users.permissions import (
    CanManageRoles,
    CanManageUsers,
    IsAdminRole,
    IsOwnerOrAdmin,
    IsTenantMember,
)
from modules.users.serializers import (
    PasswordChangeSerializer,
    RoleSerializer,
    TenantSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserRoleSerializer,
    UserSerializer,
)
from modules.users.services import RoleService, TenantService, UserService


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view using our custom serializer."""

    pass


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User CRUD operations with tenant isolation."""

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        elif self.action in ["retrieve", "me"]:
            return UserProfileSerializer
        elif self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        if not hasattr(self.request, "tenant"):
            return User.objects.none()

        queryset = (
            User.objects.filter(tenant=self.request.tenant)
            .select_related("tenant")
            .prefetch_related("user_roles__role")
        )

        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(user_roles__role__name=role).distinct()

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsTenantMember(), CanManageUsers()]
        elif self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsTenantMember(), IsOwnerOrAdmin()]
        elif self.action == "destroy":
            return [IsAuthenticated(), IsTenantMember(), IsAdminRole()]
        elif self.action in ["assign_role", "remove_role"]:
            return [IsAuthenticated(), IsTenantMember(), CanManageRoles()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = serializer.save()
        student_role = Role.objects.filter(
            tenant=self.request.tenant, name=Role.STUDENT
        ).first()
        if student_role:
            RoleService.assign_role(
                user, student_role, self.request.tenant, self.request.user
            )

    def perform_update(self, serializer):
        UserService.update_user(
            serializer.instance, serializer.validated_data, self.request.user
        )

    def perform_destroy(self, instance):
        UserService.deactivate_user(instance)

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get("role_id")

        if not role_id:
            return Response(
                {"error": "role_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role = Role.objects.get(id=role_id, tenant=request.tenant)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            user_role = RoleService.assign_role(
                user, role, request.tenant, request.user
            )
            serializer = UserRoleSerializer(user_role, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def remove_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get("role_id")

        if not role_id:
            return Response(
                {"error": "role_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role = Role.objects.get(id=role_id, tenant=request.tenant)
        except Role.DoesNotExist:
            return Response(
                {"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND
            )

        deleted = RoleService.remove_role(user, role, request.tenant)
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"error": "Role assignment not found"}, status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Role read operations."""

    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        if not hasattr(self.request, "tenant"):
            return Role.objects.none()
        return Role.objects.filter(tenant=self.request.tenant)


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for Tenant operations."""

    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Tenant.objects.none()
        return Tenant.objects.filter(id=self.request.user.tenant_id)

    def get_permissions(self):
        if self.action in ["create", "register"]:
            return [AllowAny()]
        elif self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsAdminRole()]
        return super().get_permissions()

    @action(detail=False, methods=["post"])
    def register(self, request):
        tenant_data = {
            "name": request.data.get("organization_name"),
            "subdomain": request.data.get("subdomain"),
            "subscription_plan": request.data.get("subscription_plan", "free"),
        }

        admin_user_data = {
            "username": request.data.get("username"),
            "email": request.data.get("email"),
            "password": request.data.get("password"),
            "first_name": request.data.get("first_name", ""),
            "last_name": request.data.get("last_name", ""),
        }

        required_fields = [
            "organization_name",
            "subdomain",
            "username",
            "email",
            "password",
        ]
        missing = [f for f in required_fields if not request.data.get(f)]
        if missing:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant, admin_user = TenantService.create_tenant_with_admin(
                tenant_data, admin_user_data
            )

            refresh = RefreshToken.for_user(admin_user)

            return Response(
                {
                    "message": "Tenant created successfully",
                    "tenant": TenantSerializer(tenant).data,
                    "user": UserSerializer(
                        admin_user, context={"request": request}
                    ).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ViewSets will be defined here following TDD approach
