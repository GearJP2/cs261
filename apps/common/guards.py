from rest_framework.permissions import BasePermission

class IsSessionAuthenticated(BasePermission):
    """Guard สำหรับตรวจสอบว่าผู้ใช้ล็อกอินผ่าน Server Session แล้วหรือยัง"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)