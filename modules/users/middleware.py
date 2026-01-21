"""Middleware for multi-tenant support."""

from django.utils.deprecation import MiddlewareMixin

from modules.users.models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to attach the tenant to the request object based on subdomain.

    The tenant can be identified via:
    1. HTTP_X_TENANT header (for API requests)
    2. Subdomain in the Host header (for web requests)
    """

    def process_request(self, request):
        """Extract tenant from request and attach to request object."""
        tenant = None

        # Try to get tenant from X-Tenant header (API requests)
        tenant_identifier = request.META.get("HTTP_X_TENANT")

        # If not found, try to extract from Host header
        if not tenant_identifier:
            host = request.META.get("HTTP_HOST", "").split(":")[0]
            # Extract subdomain (assumes format: subdomain.domain.com)
            parts = host.split(".")
            if len(parts) > 2:
                tenant_identifier = parts[0]

        # Look up tenant
        if tenant_identifier:
            try:
                tenant = Tenant.objects.get(subdomain=tenant_identifier, is_active=True)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                # For public endpoints (like registration), we allow no tenant
                request.tenant = None
        else:
            # No tenant identifier found
            request.tenant = None

        return None

    def process_response(self, request, response):
        """Add tenant context to response if needed."""
        return response
