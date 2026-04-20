from accounts.models import Outage
from complaints.models import Complaint


def get_customer_context(customer):
    return {
        'plan': _plan(customer),
        'balance': {'amount': str(customer.balance), 'currency': 'USD'},
        'usage_this_month': _usage(customer),
        'open_complaints': _open_complaints(customer),
        'last_payment': _last_payment(customer),
        'region': customer.region or None,
        'active_faults': _active_faults(customer),
    }


def _plan(customer):
    if not customer.plan:
        return None
    p = customer.plan
    return {
        'name': p.name,
        'monthly_price': str(p.monthly_cost),
        'data_allowance_mb': p.data_allowance_mb,
        'call_allowance_min': p.calls_allowance_min,
        'sms_allowance': p.sms_allowance,
    }


def _usage(customer):
    usage = customer.usage_records.order_by('-period_start').first()
    if not usage:
        return None
    return {
        'period_start': usage.period_start.isoformat(),
        'data_used_mb': usage.data_used_mb,
        'calls_made_min': usage.calls_used_min,
        'sms_sent': usage.sms_used,
    }


def _open_complaints(customer):
    active = [Complaint.Status.OPEN, Complaint.Status.IN_PROGRESS, Complaint.Status.ESCALATED]
    return [
        {
            'id': c.id,
            'category': c.get_category_display(),
            'status': c.get_status_display(),
            'submitted_at': c.created_at.isoformat(),
        }
        for c in customer.complaints.filter(status__in=active)
    ]


def _last_payment(customer):
    payment = customer.payments.first()
    if not payment:
        return None
    return {
        'amount': str(payment.amount),
        'date': payment.paid_at.isoformat(),
    }


def _active_faults(customer):
    if not customer.region:
        return []
    faults = Outage.objects.filter(region=customer.region, resolved_at__isnull=True)
    return [
        {
            'region': f.region,
            'description': f.description,
            'started_at': f.started_at.isoformat(),
        }
        for f in faults
    ]


CATEGORY_LABELS = {
    'plan': 'Plan',
    'balance': 'Balance',
    'usage_this_month': 'Usage',
    'open_complaints': 'Complaints',
    'last_payment': 'Payments',
    'active_faults': 'Faults',
}


def context_sources(context):
    present = []
    for key, label in CATEGORY_LABELS.items():
        value = context.get(key)
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        present.append(label)
    return present
