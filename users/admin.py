from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser , Role

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    ordering = ('-date_joined',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser','date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'info', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ('email',)
    filter_horizontal = ('user_permissions', 'groups',)

admin.site.register(CustomUser, CustomUserAdmin)





admin.site.register(Role)