from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = [
        (None, {'fields': ('username', 'password')}),
        ("Personal info", {'fields': ('first_name', 'last_name', 'email')}),
        ("Additional fields", {'fields': ('short_description',)}),
        ("Permissions", {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
        ("Important schedule",{'fields': ('last_login', 'date_joined')}),
    ]
