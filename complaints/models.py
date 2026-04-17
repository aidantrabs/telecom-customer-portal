from django.conf import settings
from django.db import models

from accounts.models import Customer


class Complaint(models.Model):
    class Category(models.TextChoices):
        BILLING = 'billing', 'Billing'
        NETWORK = 'network', 'Network'
        DEVICE = 'device', 'Device'
        ROAMING = 'roaming', 'Roaming'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        ESCALATED = 'escalated', 'Escalated'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
    )
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_category_display()} - {self.customer.account_number}'
