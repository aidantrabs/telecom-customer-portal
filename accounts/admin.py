from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Customer, Outage, Payment, Plan, Usage, User


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


@admin.register(Usage)
class UsageAdmin(admin.ModelAdmin):
    list_display = ('customer', 'period_start', 'data_used_mb', 'calls_used_min', 'sms_used')
    list_filter = ('period_start',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'paid_at')
    list_filter = ('paid_at',)


@admin.register(Outage)
class OutageAdmin(admin.ModelAdmin):
    list_display = ('region', 'started_at', 'resolved_at')
    list_filter = ('region',)
