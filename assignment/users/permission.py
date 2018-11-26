from rest_framework import permissions
from users.models import UserSession


class IsStaff(permissions.BasePermission):
    """
    Permission to allow access for Active Staff members only.
    """

    def has_permission(self, request, view):

        return request.user.is_authenticated() and request.user.is_staff


class IsActive(permissions.BasePermission):
    """
    Permission to allow access for active users only.
    """

    def has_permission(self, request, view):

        return request.user.is_active_user()


class HasValidKey(permissions.BasePermission):
    """
    Permission to allow access if valid key.
    """

    def has_permission(self, request, view):

        x = UserSession.objects.is_valid_key(request)
        print('permission', x)
        return x
