from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User

from .forms import AgentComplaintForm, ComplaintForm
from .models import Complaint


def _format_duration(td):
    if td is None:
        return 'N/A'
    total = int(td.total_seconds())
    days = total // 86400
    hours = (total % 86400) // 3600
    parts = []
    if days:
        parts.append(f'{days} day{"" if days == 1 else "s"}')
    if hours:
        parts.append(f'{hours} hour{"" if hours == 1 else "s"}')
    return ', '.join(parts) if parts else '< 1 hour'


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


@admin_required
def admin_dashboard(request):
    by_status = [
        {'label': s.label, 'count': Complaint.objects.filter(status=s).count()}
        for s in Complaint.Status
    ]
    by_category = [
        {'label': c.label, 'count': Complaint.objects.filter(category=c).count()}
        for c in Complaint.Category
    ]
    avg_duration = Complaint.objects.filter(resolved_at__isnull=False).aggregate(
        avg=Avg(ExpressionWrapper(F('resolved_at') - F('created_at'), output_field=DurationField()))
    )['avg']
    active = [Complaint.Status.OPEN, Complaint.Status.IN_PROGRESS, Complaint.Status.ESCALATED]
    breaches = Complaint.objects.filter(
        status__in=active,
        created_at__lt=timezone.now() - timedelta(days=5),
    ).order_by('created_at')

    return render(request, 'complaints/admin_dashboard.html', {
        'by_status': by_status,
        'by_category': by_category,
        'avg_resolution_display': _format_duration(avg_duration),
        'breaches': breaches,
    })
