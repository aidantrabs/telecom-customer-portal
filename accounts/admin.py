from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Customer, Plan, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'plan', 'balance', 'region')
    search_fields = ('account_number', 'user__username')
    list_filter = ('plan', 'region')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_cost', 'data_allowance_mb', 'calls_allowance_min', 'sms_allowance')
