from django.contrib import admin

from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'status', 'customer', 'assigned_agent', 'created_at', 'resolved_at')
    list_filter = ('status', 'category')
    search_fields = ('description', 'customer__account_number')
