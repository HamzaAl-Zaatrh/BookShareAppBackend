from rest_framework import permissions

class IsAdminOrReadOnly(permissions.IsAdminUser):
    
    def has_permission(self, request, view):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') 
        if request.method in permissions.SAFE_METHODS: # if (GET) request method then return True
            return True
        else:
            return bool(request.user and request.user.is_staff)

class IsOwner(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return False
        else:
            return obj.review_user == request.user or request.user.is_staff