from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import customer_required
from .models import User


@login_required
def home(request):
    role = request.user.role
    if role == User.Role.ADMIN:
        return redirect('dashboard:home')
    if role == User.Role.AGENT:
        return redirect('agent:queue')
    return redirect('complaints:list')


@customer_required
def account(request):
    customer = request.user.customer
    usage = customer.usage_records.order_by('-period_start').first()
    last_payment = customer.payments.first()
    return render(request, 'accounts/account.html', {
        'customer': customer,
        'plan': customer.plan,
        'usage': usage,
        'last_payment': last_payment,
    })
