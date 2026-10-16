from rest_framework.permissions import BasePermission

class IsOwnerFarmer(BasePermission):
    """Object-level guard for objects associated with the request user's farmer profile."""
    def has_object_permission(self, request, view, obj):
        profile = getattr(request.user, "farmer_profile", None)
        if profile is None:
            return False
        for attr in ("farmer", "owner", "profile"):
            value = getattr(obj, attr, None)
            if value is not None:
                return value == profile or value == request.user
        # Fail closed if ownership cannot be established.
        return False
