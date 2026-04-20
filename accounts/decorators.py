from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def customer_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.CUSTOMER:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def agent_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.AGENT:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def admin_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper
