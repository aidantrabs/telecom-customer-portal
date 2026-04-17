from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from accounts.models import User

from .forms import ComplaintForm
from .models import Complaint


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


@customer_required
def new_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.customer = request.user.customer
            complaint.save()
            messages.success(request, 'Your complaint has been submitted.')
            return redirect('complaints:list')
    else:
        form = ComplaintForm()
    return render(request, 'complaints/new.html', {'form': form})


@customer_required
def my_complaints(request):
    complaints = request.user.customer.complaints.all()
    return render(request, 'complaints/list.html', {'complaints': complaints})


@agent_required
def agent_queue(request):
    active_statuses = [
        Complaint.Status.OPEN,
        Complaint.Status.IN_PROGRESS,
        Complaint.Status.ESCALATED,
    ]
    complaints = request.user.assigned_complaints.filter(
        status__in=active_statuses
    ).order_by('created_at')
    return render(request, 'complaints/agent_queue.html', {'complaints': complaints})
