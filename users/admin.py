from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role


admin.site.register(Role)
class ServiceTypeFilter(admin.SimpleListFilter):
    title = 'service type'
    parameter_name = 'service_type'

    def lookups(self, request, model_admin):
        return (
            ('Photography', 'Photography'),
            ('Videography', 'Videography'),
            ('DJ', 'DJ'),
            ('Photobooth', 'Photobooth'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role__service_type__name=self.value())
        return queryset


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        'username', 'user_type', 'first_name', 'last_name', 'email', 'primary_phone1', 'primary_address1',
        'city', 'state', 'postal_code', 'is_staff', 'is_active', 'role', 'get_service_type',
    )
    list_filter = ('username', 'email', 'is_staff', 'is_active', 'role', 'additional_roles', ServiceTypeFilter)
    fieldsets = (
        (None, {'fields': ('username', 'password', 'user_type', 'email', 'profile_picture', 'website', 'role', 'additional_roles', 'status')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'primary_phone1', 'primary_phone2', 'primary_address1', 'primary_address2', 'city', 'state', 'postal_code')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'primary_phone1', 'primary_address1', 'city', 'state', 'postal_code', 'is_staff', 'is_active', 'role')}
        ),
    )
    search_fields = ('username', 'email',)
    ordering = ('username', 'email',)

    def get_service_type(self, obj):
        return "Test Service Type"


admin.site.register(CustomUser, CustomUserAdmin)


