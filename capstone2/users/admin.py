from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin

from users.models import User, DormInfo, Profile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = [
        (None, {'fields': ('username', 'password')}),
        ("Personal info", {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ("Permissions", {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
        ("Important schedule",{'fields': ('last_login', 'date_joined')}),
    ]

@admin.register(DormInfo)
class DormInfoAdmin(ModelAdmin):
    fieldsets = [
        (None, {'fields': ('user', 'name', 'sex')}),
        ("Application info", {'fields': ('application_order', 'building', 'room', 'residency_period', 'is_accepted')}),
    ]

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    fieldsets = [
        (None, {'fields': ('user',)}),
        ("Profile info", {'fields': ('is_smoker', 'has_sleeping_habits', 'lifestyle_pattern', 'eat_in_room')}),
    ]