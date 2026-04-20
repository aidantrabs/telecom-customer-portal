from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import User


def customer_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.CUSTOMER:
            return redirect('home')
        return view(request, *args, **kwargs)
    return wrapper


def agent_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.AGENT:
            return redirect('home')
        return view(request, *args, **kwargs)
    return wrapper


def admin_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            return redirect('home')
        return view(request, *args, **kwargs)
    return wrapper
