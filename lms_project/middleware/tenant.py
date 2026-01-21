"""
Tenant middleware for extracting and setting tenant context.
"""

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from modules.users.models import Tenant


class TenantMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = [
        "/admin/",
        "/api/v1/auth/token/",
        "/api/v1/auth/register/",
        "/api/v1/tenants/",
    ]

    def process_request(self, request):
        if self._should_skip_tenant_check(request):
            return None

        tenant = self._extract_tenant_from_request(request)

        if not tenant:
            return self._tenant_not_found_response()

        if not tenant.is_active:
            return self._tenant_inactive_response()

        request.tenant = tenant
        return None

    def _should_skip_tenant_check(self, request):
        return any(request.path.startswith(path) for path in self.EXCLUDED_PATHS)

    def _extract_tenant_from_request(self, request):
        tenant = (
            self._get_tenant_from_jwt(request)
            or self._get_tenant_from_header(request)
            or self._get_tenant_from_subdomain(request)
        )
        return tenant

    def _get_tenant_from_jwt(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            tenant_id = payload.get("tenant_id")

            if tenant_id:
                return Tenant.objects.filter(id=tenant_id, is_active=True).first()
        except (jwt.DecodeError, jwt.InvalidTokenError):
            pass

        return None

    def _get_tenant_from_subdomain(self, request):
        host = request.get_host().split(":")[0]
        subdomain = self._extract_subdomain(host)

        if subdomain:
            return Tenant.objects.filter(subdomain=subdomain, is_active=True).first()

        return None

    def _get_tenant_from_header(self, request):
        subdomain = request.headers.get("X-Tenant") or request.META.get("HTTP_X_TENANT")

        if subdomain:
            return Tenant.objects.filter(subdomain=subdomain, is_active=True).first()

        return None

    def _extract_subdomain(self, host):
        parts = host.split(".")

        if len(parts) > 2 and parts[0] not in ["www", "api"]:
            return parts[0]

        return None

    def _tenant_not_found_response(self):
        return JsonResponse({"error": "Tenant not found or invalid"}, status=400)

    def _tenant_inactive_response(self):
        return JsonResponse({"error": "Tenant is inactive"}, status=403)
