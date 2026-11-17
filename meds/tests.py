from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from meds import ai
from meds.models import Medication

PASSWORD = "a-long-pass-987"
VALID = {
    "name": "metformin",
    "dose_amount": "500",
    "dose_unit": "mg",
    "route": "oral",
    "times_per_day": "2",
    "meal_timing": "with",
    "start_date": "2026-11-01",
    "end_date": "",
}


def make_user(username):
    return get_user_model().objects.create_user(username, password=PASSWORD)


class AddMedicationTests(TestCase):
    def setUp(self):
        self.user = make_user("alice@example.com")
        self.client.login(username="alice@example.com", password=PASSWORD)

    def post(self, **changes):
        return self.client.post(reverse("medication_add"), {**VALID, **changes})

    def test_add_page_requires_login(self):
        self.client.logout()
        url = reverse("medication_add")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_add_page_loads_with_today_as_start_date(self):
        response = self.client.get(reverse("medication_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'value="{timezone.localdate():%Y-%m-%d}"')

    def test_valid_medication_is_saved_for_the_logged_in_user(self):
        response = self.post()
        self.assertRedirects(response, reverse("home"))
        med = Medication.objects.get()
        self.assertEqual(med.user, self.user)
        self.assertEqual(med.dose_amount, Decimal("500"))
        self.assertEqual(med.times_per_day, 2)
        self.assertEqual(med.meal_timing, "with")
        self.assertIsNone(med.end_date)

    def test_success_message_and_med_appear_on_list(self):
        response = self.client.post(reverse("medication_add"), VALID, follow=True)
        self.assertContains(response, "Added metformin.")
        self.assertContains(response, "500 mg")
        self.assertContains(response, "Twice daily")

    def test_required_fields(self):
        for field in ["name", "dose_amount", "dose_unit", "times_per_day", "start_date"]:
            with self.subTest(field=field):
                response = self.post(**{field: ""})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "This field is required.")
                self.assertContains(response, "alert alert-danger")
        self.assertEqual(Medication.objects.count(), 0)

    def test_dose_must_be_positive(self):
        for amount in ["0", "-5"]:
            with self.subTest(amount=amount):
                response = self.post(dose_amount=amount)
                self.assertContains(response, "is-invalid")
        self.assertEqual(Medication.objects.count(), 0)

    def test_end_date_cannot_be_before_start_date(self):
        response = self.post(start_date="2026-11-10", end_date="2026-11-09")
        self.assertContains(response, "End date cannot be earlier than the start date.")
        self.assertEqual(Medication.objects.count(), 0)

    def test_end_date_on_start_date_is_allowed(self):
        self.post(start_date="2026-11-10", end_date="2026-11-10")
        self.assertEqual(Medication.objects.get().end_date, date(2026, 11, 10))

    def test_invalid_choice_is_rejected(self):
        response = self.post(route="by-magic")
        self.assertContains(response, "Select a valid choice.")
        self.assertEqual(Medication.objects.count(), 0)

    def test_route_and_meal_timing_are_separate_fields(self):
        self.post(route="nasal", meal_timing="before")
        med = Medication.objects.get()
        self.assertEqual((med.route, med.meal_timing), ("nasal", "before"))

    def test_user_field_cannot_be_posted(self):
        other = make_user("bob@example.com")
        self.post(user=other.pk)
        self.assertEqual(Medication.objects.get().user, self.user)


class MedicationListTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice@example.com")
        self.bob = make_user("bob@example.com")
        start = date(2026, 11, 1)
        Medication.objects.create(user=self.alice, name="metformin", dose_amount=Decimal("500"),
                                  dose_unit="mg", times_per_day=2, start_date=start)
        Medication.objects.create(user=self.bob, name="warfarin", dose_amount=Decimal("5"),
                                  dose_unit="mg", times_per_day=1, start_date=start)

    def test_list_shows_only_own_medications(self):
        self.client.login(username="alice@example.com", password=PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "metformin")
        self.assertNotContains(response, "warfarin")

    def test_medications_persist_after_logout_and_login(self):
        self.client.login(username="alice@example.com", password=PASSWORD)
        self.client.post(reverse("logout"))
        self.client.login(username="alice@example.com", password=PASSWORD)
        self.assertContains(self.client.get(reverse("home")), "metformin")

    def test_empty_state(self):
        make_user("carol@example.com")
        self.client.login(username="carol@example.com", password=PASSWORD)
        self.assertContains(self.client.get(reverse("home")), "You haven't added any medications yet.")

    def test_dose_display_drops_trailing_zeros(self):
        med = Medication(dose_amount=Decimal("1.50"), dose_unit="tablet")
        self.assertEqual(med.dose, "1.5 tablet(s)")


class MedicationSeedTests(TestCase):
    @mock.patch.dict("os.environ", {"SEED_ADMIN_PASSWORD": "a-pw-123456", "SEED_MEMBER_PASSWORD": "m-pw-123456"})
    def test_seed_adds_demo_medications_once(self):
        call_command("seed", stdout=mock.MagicMock())
        call_command("seed", stdout=mock.MagicMock())
        member = get_user_model().objects.get(username="member@example.com")
        self.assertEqual(member.medications.count(), 3)
        self.assertTrue(all(m.start_date <= timezone.localdate() - timedelta(days=1) for m in member.medications.all()))
        admin = get_user_model().objects.get(username="admin@example.com")
        self.assertEqual(admin.medications.count(), 0)


@override_settings(OPENROUTER_API_KEY="test-key", OPENROUTER_MODEL="test-model")
class OpenRouterClientTests(SimpleTestCase):
    @mock.patch("meds.ai.requests.post")
    def test_returns_message_text(self, post):
        post.return_value.json.return_value = {"choices": [{"message": {"content": "hi"}}]}
        self.assertEqual(ai.call_openrouter([{"role": "user", "content": "x"}]), "hi")

    @mock.patch("meds.ai.requests.post", side_effect=ai.requests.ConnectionError("down"))
    def test_network_failure_raises_ai_unavailable(self, post):
        with self.assertRaises(ai.AIUnavailable):
            ai.call_openrouter([{"role": "user", "content": "x"}])

    @override_settings(OPENROUTER_API_KEY="")
    def test_missing_key_raises_ai_unavailable(self):
        with self.assertRaises(ai.AIUnavailable):
            ai.call_openrouter([])
