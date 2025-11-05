from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin

from users.models import User, DormInfo, Profile

class CustomUserAdmin(UserAdmin):
    list_display = ('nickname', 'application_order', 'is_staff')
    ordering = ('nickname', )
    search_fields = ('nickname',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('nickname', 'application_order'),
        }),
    )

    fieldsets = [
        (None, {"fields": ("nickname", 'application_order', 'is_staff')}),
    ]

admin.site.register(User, CustomUserAdmin)

admin.site.register(DormInfo)
admin.site.register(Profile)