from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken

class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_verified", "is_staff")
    search_fields = ("email", "full_name", "employee_id")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "department", "employee_id", "supervisor", "is_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password1", "password2", "role")}),
    )

    filter_horizontal = ("groups", "user_permissions")

admin.site.register(User, UserAdmin)
admin.site.register(EmailVerificationToken)
