from rest_framework import permissions

class IsSystemOwner(permissions.BasePermission):
    """Allows access only to SystemOwner."""
    def has_permission(self, request, view):
        print(f"==>> request.user: {request.user}")
        return request.user.is_authenticated and request.user.role == "system_owner"

class IsSystemOwnerOrOrganization(permissions.BasePermission):
    """Allows access only to SystemOwner or Organization."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["system_owner", "organization"]

class IsSystemOwnerOrOrganizationOrAdmin(permissions.BasePermission):
    """Allows access only to SystemOwner, Organization, or Admin."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["system_owner", "organization", "admin"]


class IsOrganization(permissions.BasePermission):
    """Allows access only to SystemOwner or Organization."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "organization"  # Changed from `in` to exact equality

class IsAdmin(permissions.BasePermission):
    """Allows access only to SystemOwner, Organization, or Admin."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"  # Changed from `in` to exact equality
