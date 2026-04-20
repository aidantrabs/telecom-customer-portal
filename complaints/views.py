from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User

from .forms import AgentComplaintForm, ComplaintForm
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


@agent_required
def agent_complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, assigned_agent=request.user)

    if request.method == 'POST':
        form = AgentComplaintForm(request.POST, complaint=complaint)
        if form.is_valid():
            complaint.status = form.cleaned_data['status']
            note = form.cleaned_data['notes_append'].strip()
            if note:
                stamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                entry = f'[{stamp} {request.user.username}] {note}'
                if complaint.internal_notes:
                    complaint.internal_notes = f'{complaint.internal_notes}\n\n{entry}'
                else:
                    complaint.internal_notes = entry
            complaint.save()
            messages.success(request, 'Complaint updated.')
            return redirect('agent:detail', pk=complaint.pk)
    else:
        form = AgentComplaintForm(complaint=complaint)

    return render(request, 'complaints/agent_detail.html', {
        'complaint': complaint,
        'form': form,
    })
