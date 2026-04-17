from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        AGENT = 'agent', 'Agent'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)


class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    data_allowance_mb = models.IntegerField()
    calls_allowance_min = models.IntegerField()
    sms_allowance = models.IntegerField()
    monthly_cost = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer')
    account_number = models.CharField(max_length=20, unique=True)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, null=True, blank=True, related_name='customers')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    region = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.account_number


class Usage(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='usage_records')
    period_start = models.DateField()
    data_used_mb = models.IntegerField(default=0)
    calls_used_min = models.IntegerField(default=0)
    sms_used = models.IntegerField(default=0)

    class Meta:
        unique_together = ('customer', 'period_start')
        ordering = ['-period_start']

    def __str__(self):
        return f'{self.customer.account_number} - {self.period_start}'


class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField()

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.customer.account_number} - ${self.amount} on {self.paid_at:%Y-%m-%d}'
