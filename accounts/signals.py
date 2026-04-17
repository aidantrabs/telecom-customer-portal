from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Customer, User


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.role != User.Role.CUSTOMER:
        return
    if Customer.objects.filter(user=instance).exists():
        return
    Customer.objects.create(
        user=instance,
        account_number=f'DGT-{instance.pk:05d}',
    )
