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
        ("Profile info", {'fields': ('smoking_type', 'smoking_amount', 'sleeping_habit', 'sleeping_habit_freq', 'sleeping_habit_extent', 'life_style', 'wake_up_time', 'bed_time', 'pre_sleeping_life_style', 'sensitivity_to_sleep', 'cleaning_cycle', 'eating_in_room')}),
    ]