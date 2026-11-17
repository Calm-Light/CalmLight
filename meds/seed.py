"""Demo medications for the member grader account. Called by `python manage.py seed`."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from meds.models import Medication

DEMO_USER = "member@example.com"

# Fake demo data only.
DEMO_MEDICATIONS = [
    {"name": "metformin", "dose_amount": Decimal("500"), "dose_unit": "mg", "route": "oral",
     "times_per_day": 2, "meal_timing": "with"},
    {"name": "lisinopril", "dose_amount": Decimal("10"), "dose_unit": "mg", "route": "oral",
     "times_per_day": 1, "meal_timing": "none"},
    {"name": "fluticasone", "dose_amount": Decimal("2"), "dose_unit": "puff", "route": "nasal",
     "times_per_day": 1, "meal_timing": "none"},
]


def seed(stdout):
    user = get_user_model().objects.get(username=DEMO_USER)
    start = timezone.localdate() - timedelta(days=14)
    for data in DEMO_MEDICATIONS:
        _, created = Medication.objects.get_or_create(
            user=user, name=data["name"], defaults={**data, "start_date": start}
        )
        if created:
            stdout.write(f"created demo medication {data['name']}")
