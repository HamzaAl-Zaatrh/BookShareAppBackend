from rest_framework import permissions

class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.book_owner_id.id == request.user.id or request.user.is_staff
        else:
            # print(obj.book_owner_id.id, request.user.id )
            return obj.book_owner_id.id == request.user.id or request.user.is_staff
        