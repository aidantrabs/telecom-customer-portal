from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import User


@login_required
def home(request):
    role = request.user.role
    if role == User.Role.ADMIN:
        return redirect('dashboard:home')
    if role == User.Role.AGENT:
        return redirect('agent:queue')
    return redirect('complaints:list')
