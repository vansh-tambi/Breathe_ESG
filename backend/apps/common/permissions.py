from django.conf import settings
from rest_framework.permissions import BasePermission

class IsAuthenticatedOrLocal(BasePermission):
    """
    Development-only bypass: allow requests without authentication if settings.DEBUG is True,
    otherwise require standard authenticated access.
    """
    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        return bool(request.user and request.user.is_authenticated)
