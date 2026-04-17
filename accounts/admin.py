from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Customer, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user')
    search_fields = ('account_number', 'user__username')
