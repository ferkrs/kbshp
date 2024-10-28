from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, BarberProfile, Client, AttendanceLog

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'display_image')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'image')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Información Adicional', {'fields': ('role',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'image'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 45px; height:45px;" />', obj.image.url)
        return ''
    display_image.short_description = 'Imagen'

admin.site.register(User, UserAdmin)

# Registrar otros modelos si aún no lo has hecho
admin.site.register(BarberProfile)
admin.site.register(Client)
admin.site.register(AttendanceLog)