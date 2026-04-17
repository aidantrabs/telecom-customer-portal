from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ComplaintForm


@login_required
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


@login_required
def my_complaints(request):
    complaints = request.user.customer.complaints.all()
    return render(request, 'complaints/list.html', {'complaints': complaints})
