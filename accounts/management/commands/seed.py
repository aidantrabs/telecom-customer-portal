from datetime import timedelta
from decimal import Decimal
from random import randint, seed as random_seed

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Customer, Outage, Payment, Plan, Usage, User
from complaints.models import Complaint


PLANS = [
    {
        'name': 'Basic',
        'data_allowance_mb': 2048,
        'calls_allowance_min': 100,
        'sms_allowance': 100,
        'monthly_cost': Decimal('15.00'),
    },
    {
        'name': 'Standard',
        'data_allowance_mb': 10240,
        'calls_allowance_min': 500,
        'sms_allowance': 500,
        'monthly_cost': Decimal('35.00'),
    },
    {
        'name': 'Premium',
        'data_allowance_mb': 51200,
        'calls_allowance_min': 2000,
        'sms_allowance': 2000,
        'monthly_cost': Decimal('75.00'),
    },
]

CUSTOMER_REGIONS = [
    'Port of Spain',
    'San Fernando',
    'Chaguanas',
    'Arima',
    'Tunapuna',
]


class Command(BaseCommand):
    help = 'seed the database with sample data for development and review'

    def handle(self, *args, **options):
        if User.objects.filter(role=User.Role.CUSTOMER).exists():
            self.stdout.write('database already seeded, skipping')
            return

        random_seed(42)

        with transaction.atomic():
            plans = self._create_plans()
            self._create_admin()
            agents = self._create_agents()
            customers = self._create_customers(plans)
            self._create_payments(customers)
            self._create_usage(customers)
            self._create_outages()
            self._create_complaints(customers, agents)

        self.stdout.write(self.style.SUCCESS('seed complete'))

    def _create_plans(self):
        plans = []

        for plan_data in PLANS:
            plan = Plan.objects.create(**plan_data)
            plans.append(plan)

        return plans

    def _create_admin(self):
        User.objects.create_user(
            'portal_admin',
            email='admin@notdigicel.com',
            password='admin123',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )

    def _create_agents(self):
        agents = []

        for i in range(1, 4):
            agent = User.objects.create_user(
                f'agent{i}',
                email=f'agent{i}@notdigicel.com',
                password='agent123',
                role=User.Role.AGENT,
            )
            agents.append(agent)

        return agents

    def _create_customers(self, plans):
        customers = []

        for i, region in enumerate(CUSTOMER_REGIONS, start=1):
            user = User.objects.create_user(
                f'customer{i}',
                email=f'customer{i}@example.com',
                password='customer123',
                role=User.Role.CUSTOMER,
            )

            # signal auto-created the customer profile, fill in the real fields
            customer = Customer.objects.get(user=user)
            customer.account_number = f'DGT-{10000 + i:05d}'
            customer.plan = plans[(i - 1) % len(plans)]
            customer.balance = Decimal(randint(0, 200))
            customer.region = region
            customer.save()

            customers.append(customer)

        return customers

    def _create_payments(self, customers):
        now = timezone.now()

        for customer in customers:
            for months_ago in range(3):
                offset_days = 30 * months_ago + randint(1, 5)

                Payment.objects.create(
                    customer=customer,
                    amount=customer.plan.monthly_cost,
                    paid_at=now - timedelta(days=offset_days),
                )

    def _create_usage(self, customers):
        period_start = timezone.now().date().replace(day=1)

        for customer in customers:
            Usage.objects.create(
                customer=customer,
                period_start=period_start,
                data_used_mb=randint(100, customer.plan.data_allowance_mb),
                calls_used_min=randint(10, customer.plan.calls_allowance_min),
                sms_used=randint(0, customer.plan.sms_allowance),
            )

    def _create_outages(self):
        now = timezone.now()

        Outage.objects.create(
            region='Port of Spain',
            description='fiber cut affecting mobile data and voice services in POS',
            started_at=now - timedelta(hours=4),
            resolved_at=None,
        )

        Outage.objects.create(
            region='San Fernando',
            description='tower maintenance causing bad reception',
            started_at=now - timedelta(days=2),
            resolved_at=now - timedelta(days=1),
        )

    def _create_complaints(self, customers, agents):
        categories = list(Complaint.Category)
        statuses = list(Complaint.Status)

        for i in range(15):
            status = statuses[i % len(statuses)]
            category = categories[i % len(categories)]
            customer = customers[i % len(customers)]

            if status == Complaint.Status.OPEN:
                agent = None
            else:
                agent = agents[i % len(agents)]

            if status in (Complaint.Status.RESOLVED, Complaint.Status.CLOSED):
                notes = 'resolved per standard procedure'
            else:
                notes = ''

            description = f'sample {category.label.lower()} complaint about service in {customer.region}'

            complaint = Complaint.objects.create(
                customer=customer,
                category=category,
                description=description,
                status=status,
                assigned_agent=agent,
                internal_notes=notes,
            )

            # backdate so sla breach detection has data to work with
            created = timezone.now() - timedelta(days=i, hours=randint(0, 23))
            updates = {'created_at': created}

            if status in (Complaint.Status.RESOLVED, Complaint.Status.CLOSED):
                updates['resolved_at'] = created + timedelta(hours=randint(2, 48))

            Complaint.objects.filter(pk=complaint.pk).update(**updates)
