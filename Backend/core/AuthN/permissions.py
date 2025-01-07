from rest_framework import permissions

class IsSystemOwner(permissions.BasePermission):
    """
    Custom permission to only allow SystemOwners to register an Organization.
    """
    def has_permission(self, request, view):
        print("_________________-sdsds")
        # Ensure the user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if the user is a SystemOwner
        if not hasattr(request.user, 'systemowner'):
            return False

        return True
