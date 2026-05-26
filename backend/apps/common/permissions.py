from rest_framework.permissions import BasePermission

class IsAuthenticatedOrLocal(BasePermission):
    """
    Allow requests from localhost for prototype validation, 
    otherwise require authenticated access.
    """
    def has_permission(self, request, view):
        if request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1'):
            return True
        return request.user and request.user.is_authenticated
