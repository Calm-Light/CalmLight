"""
python manage.py seed

Creates the demo / grader accounts. Safe to run any number of times:
accounts are created if missing and their password and role are reset.
Passwords come from environment variables so they are never in git.

To add demo data for another app, write a function `seed(stdout)` in that
app (e.g. meds/seed.py) and add it to EXTRA_SEEDERS below.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

ACCOUNTS = [
    # (username/email, password env var, is_staff/is_superuser)
    ("admin@example.com", "SEED_ADMIN_PASSWORD", True),
    ("member@example.com", "SEED_MEMBER_PASSWORD", False),
]

EXTRA_SEEDERS = [
    # "meds.seed.seed",
]


class Command(BaseCommand):
    help = "Create or update demo and grader accounts (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        for email, password_var, is_admin in ACCOUNTS:
            password = os.environ.get(password_var)
            if not password:
                raise CommandError(f"Set {password_var} before running seed.")
            user, created = User.objects.get_or_create(username=email, defaults={"email": email})
            user.email = email
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.set_password(password)
            user.save()
            self.stdout.write(f"{'created' if created else 'updated'} {email}")

        from django.utils.module_loading import import_string

        for path in EXTRA_SEEDERS:
            import_string(path)(self.stdout)

        self.stdout.write(self.style.SUCCESS("Seed complete."))
