from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from meds import ai
from meds.models import AIRequest, Medication

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


class CleanLabelFieldsTests(SimpleTestCase):
    """The AI's answer is never trusted as-is."""

    def test_keeps_valid_values(self):
        fields, missing = ai.clean_label_fields({
            "name": "  Metformin  ", "dose_amount": 500, "dose_unit": "mg", "route": "oral",
            "times_per_day": 2, "meal_timing": "with",
        })
        self.assertEqual(fields, {"name": "Metformin", "dose_amount": Decimal("500"), "dose_unit": "mg",
                                  "route": "oral", "times_per_day": 2, "meal_timing": "with"})
        self.assertEqual(missing, [])

    def test_drops_invalid_values_and_reports_them_missing(self):
        fields, missing = ai.clean_label_fields({
            "name": "", "dose_amount": -5, "dose_unit": "spoonful", "route": "by magic",
            "times_per_day": 7, "meal_timing": "whenever",
        })
        self.assertEqual(fields, {})
        self.assertEqual(missing, ["name", "dose", "unit", "route", "how often", "meal instructions"])

    def test_nulls_and_odd_types(self):
        fields, _ = ai.clean_label_fields({"name": None, "dose_amount": True, "times_per_day": "2"})
        self.assertEqual(fields, {})
        self.assertEqual(ai.clean_label_fields("not a dict"), ({}, list(ai.FIELD_LABELS.values())))

    def test_dose_amount_from_string_and_float(self):
        self.assertEqual(ai.clean_label_fields({"dose_amount": "2.5"})[0]["dose_amount"], Decimal("2.5"))
        self.assertEqual(ai.clean_label_fields({"dose_amount": 0.5})[0]["dose_amount"], Decimal("0.5"))
        self.assertNotIn("dose_amount", ai.clean_label_fields({"dose_amount": "NaN"})[0])

    def test_whole_number_doses_show_as_plain_digits(self):
        for raw, shown in [(500, "500"), (10, "10"), (1000, "1000"), ("100.00", "100"), (2.5, "2.5"), (0.25, "0.25")]:
            self.assertEqual(str(ai.clean_label_fields({"dose_amount": raw})[0]["dose_amount"]), shown)


@override_settings(OPENROUTER_API_KEY="test-key", OPENROUTER_MODEL="test-model")
class ParseLabelTests(SimpleTestCase):
    @mock.patch("meds.ai.requests.post")
    def test_sends_schema_and_only_label_text(self, post):
        post.return_value.json.return_value = {"choices": [{"message": {"content": '{"name": "metformin"}'}}]}
        fields, _ = ai.parse_label("Metformin 500 mg twice daily")
        self.assertEqual(fields, {"name": "metformin"})
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["response_format"]["type"], "json_schema")
        self.assertTrue(payload["response_format"]["json_schema"]["strict"])
        self.assertEqual(payload["messages"][1], {"role": "user", "content": "Metformin 500 mg twice daily"})

    @mock.patch("meds.ai.call_openrouter", return_value='```json\n{"name": "lisinopril"}\n```')
    def test_accepts_json_in_code_fence(self, _):
        self.assertEqual(ai.parse_label("x")[0], {"name": "lisinopril"})

    @mock.patch("meds.ai.call_openrouter", return_value="Sorry, I can't help with that.")
    def test_non_json_reply_raises_ai_unavailable(self, _):
        with self.assertRaises(ai.AIUnavailable):
            ai.parse_label("x")

    @mock.patch("meds.ai.requests.post")
    def test_empty_content_raises_ai_unavailable(self, post):
        post.return_value.json.return_value = {"choices": [{"message": {"content": None}}]}
        with self.assertRaises(ai.AIUnavailable):
            ai.parse_label("x")

    @mock.patch("meds.ai.call_openrouter", return_value="{}")
    def test_long_text_is_truncated(self, call):
        ai.parse_label("a" * 5000)
        self.assertEqual(len(call.call_args.args[0][1]["content"]), ai.MAX_LABEL_CHARS)


FILLED = ({"name": "metformin", "dose_amount": Decimal("500"), "dose_unit": "mg", "route": "oral",
           "times_per_day": 2, "meal_timing": "with"}, [])


@override_settings(AI_DAILY_LIMIT=3)
class SmartAddViewTests(TestCase):
    def setUp(self):
        self.user = make_user("alice@example.com")
        self.client.login(username="alice@example.com", password=PASSWORD)
        self.url = reverse("medication_fill")

    def fill(self, text="Metformin 500 mg tablet, take 1 twice daily with meals"):
        return self.client.post(self.url, {"label_text": text})

    @mock.patch("meds.views.ai.parse_label", return_value=FILLED)
    def test_fills_form_but_saves_nothing(self, parse):
        response = self.fill()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="metformin"')
        self.assertContains(response, '<option value="mg" selected>')
        self.assertContains(response, "Check every field before you save")
        self.assertEqual(Medication.objects.count(), 0)
        parse.assert_called_once()

    @override_settings(OPENROUTER_API_KEY="test-key", OPENROUTER_MODEL="test-model")
    @mock.patch("meds.ai.call_openrouter", return_value='{"name": "metformin", "dose_amount": 500}')
    def test_filled_dose_shows_plain_digits(self, _):
        response = self.fill()
        self.assertContains(response, 'name="dose_amount" value="500"')
        self.assertNotContains(response, "5E+2")

    @mock.patch("meds.views.ai.parse_label", return_value=({"name": "metformin"}, ["dose", "unit", "how often"]))
    def test_lists_fields_the_user_must_fill(self, _):
        self.assertContains(self.fill(), "Please fill in: dose, unit, how often.")

    @mock.patch("meds.views.ai.parse_label", side_effect=ai.AIUnavailable("down"))
    def test_ai_failure_shows_message_and_keeps_manual_form(self, _):
        response = self.fill()
        self.assertContains(response, "AI fill isn&#x27;t available right now")
        self.assertContains(response, 'name="dose_amount"')
        usage = AIRequest.objects.get()
        self.assertFalse(usage.succeeded)

    @mock.patch("meds.views.ai.parse_label", return_value=({}, list(ai.FIELD_LABELS.values())))
    def test_nothing_found(self, _):
        self.assertContains(self.fill("hello"), "couldn&#x27;t find medication details")

    @mock.patch("meds.views.ai.parse_label", return_value=FILLED)
    def test_daily_limit_blocks_extra_calls(self, parse):
        for _ in range(3):
            self.fill()
        response = self.fill()
        self.assertContains(response, "reached today&#x27;s limit")
        self.assertEqual(parse.call_count, 3)
        self.assertContains(response, "0 AI fills left today")

    @mock.patch("meds.views.ai.parse_label", return_value=FILLED)
    def test_limit_is_per_user(self, parse):
        for _ in range(3):
            self.fill()
        make_user("bob@example.com")
        self.client.login(username="bob@example.com", password=PASSWORD)
        self.fill()
        self.assertEqual(parse.call_count, 4)

    @mock.patch("meds.views.ai.parse_label")
    def test_empty_text_does_not_call_ai(self, parse):
        response = self.fill("")
        self.assertContains(response, "This field is required.")
        parse.assert_not_called()
        self.assertEqual(AIRequest.objects.count(), 0)

    def test_requires_login_and_post(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.client.logout()
        self.assertRedirects(self.fill(), f"{reverse('login')}?next={self.url}", fetch_redirect_response=False)

    @mock.patch("meds.views.ai.parse_label", return_value=FILLED)
    def test_user_can_save_the_filled_form(self, _):
        self.fill()
        self.client.post(reverse("medication_add"), {**VALID})
        self.assertEqual(Medication.objects.get().user, self.user)


class EditStopDeleteTests(TestCase):
    def setUp(self):
        self.user = make_user("alice@example.com")
        self.other = make_user("bob@example.com")
        self.client.login(username="alice@example.com", password=PASSWORD)
        self.today = timezone.localdate()
        self.med = self.make_med(self.user, "metformin", start_date=self.today - timedelta(days=30))

    @staticmethod
    def make_med(user, name, **extra):
        fields = {"dose_amount": Decimal("500"), "dose_unit": "mg", "times_per_day": 2,
                  "start_date": date(2026, 11, 1), **extra}
        return Medication.objects.create(user=user, name=name, **fields)

    def url(self, name, med=None):
        return reverse(name, args=[(med or self.med).pk])

    # --- edit ---
    def test_edit_page_shows_current_values_without_ai_card(self):
        response = self.client.get(self.url("medication_edit"))
        self.assertContains(response, "Edit metformin")
        self.assertContains(response, 'value="metformin"')
        self.assertContains(response, 'value="500.00"')
        self.assertNotContains(response, "Fill in with AI")
        self.assertContains(response, self.url("medication_delete"))

    def test_edit_saves_changes(self):
        data = {**VALID, "dose_amount": "1000", "times_per_day": "3", "route": "oral", "meal_timing": "after",
                "start_date": "2026-10-01", "end_date": "2027-01-31"}
        response = self.client.post(self.url("medication_edit"), data, follow=True)
        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Saved changes to metformin.")
        self.med.refresh_from_db()
        self.assertEqual((self.med.dose_amount, self.med.times_per_day, self.med.meal_timing),
                         (Decimal("1000"), 3, "after"))
        self.assertEqual((self.med.start_date, self.med.end_date), (date(2026, 10, 1), date(2027, 1, 31)))
        self.assertContains(response, "1000 mg")

    def test_edit_rejects_invalid_values_and_keeps_old_data(self):
        response = self.client.post(self.url("medication_edit"),
                                    {**VALID, "name": "", "start_date": "2026-11-10", "end_date": "2026-11-01"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit metformin")  # heading keeps the saved name
        self.assertContains(response, "End date cannot be earlier than the start date.")
        self.med.refresh_from_db()
        self.assertEqual(self.med.name, "metformin")
        self.assertIsNone(self.med.end_date)

    def test_edit_cannot_change_the_owner(self):
        self.client.post(self.url("medication_edit"), {**VALID, "user": self.other.pk})
        self.med.refresh_from_db()
        self.assertEqual(self.med.user, self.user)

    # --- stop / restart ---
    def test_stop_asks_first_and_get_changes_nothing(self):
        response = self.client.get(self.url("medication_stop"))
        self.assertContains(response, "Stop taking metformin?")
        self.med.refresh_from_db()
        self.assertIsNone(self.med.discontinued_on)

    def test_stop_moves_medication_to_past(self):
        response = self.client.post(self.url("medication_stop"), follow=True)
        self.med.refresh_from_db()
        self.assertEqual((self.med.discontinued_on, self.med.end_date), (self.today, None))
        self.assertEqual(list(response.context["medications"]), [])
        self.assertEqual(list(response.context["past_medications"]), [self.med])
        self.assertContains(response, "Past medications")
        self.assertContains(response, f"Stopped {self.today:%b} {self.today.day}, {self.today.year}")
        self.assertContains(response, "You aren't taking any medications right now.")

    def test_stop_and_restart_keep_the_planned_end_date(self):
        # Reported in review: end Nov 24, stopped by mistake, restarted -> must still end Nov 24.
        planned_end = self.today + timedelta(days=7)
        self.med.end_date = planned_end
        self.med.save()
        self.client.post(self.url("medication_stop"))
        self.med.refresh_from_db()
        self.assertEqual((self.med.discontinued_on, self.med.end_date), (self.today, planned_end))
        self.assertIn(self.med, Medication.objects.past())
        self.client.post(self.url("medication_resume"))
        self.med.refresh_from_db()
        self.assertEqual((self.med.discontinued_on, self.med.end_date), (None, planned_end))
        self.assertIn(self.med, Medication.objects.active())

    def test_restart_after_end_date_passed_explains_why_it_stays_past(self):
        old = self.make_med(self.user, "amoxicillin", start_date=self.today - timedelta(days=10),
                            end_date=self.today - timedelta(days=1), discontinued_on=self.today - timedelta(days=5))
        response = self.client.post(self.url("medication_resume", old), follow=True)
        old.refresh_from_db()
        self.assertIsNone(old.discontinued_on)
        self.assertEqual(list(response.context["past_medications"]), [old])
        self.assertContains(response, "has passed, so it stays under Past medications")

    def test_stop_before_start_date_does_not_break_the_date_rule(self):
        future = self.make_med(self.user, "lisinopril", start_date=self.today + timedelta(days=3))
        self.client.post(self.url("medication_stop", future))
        future.refresh_from_db()
        self.assertEqual(future.discontinued_on, self.today)
        self.assertIsNone(future.end_date)
        self.assertIn(future, Medication.objects.past())

    def test_restart_undoes_stop(self):
        self.client.post(self.url("medication_stop"))
        response = self.client.post(self.url("medication_resume"), follow=True)
        self.med.refresh_from_db()
        self.assertIsNone(self.med.discontinued_on)
        self.assertIsNone(self.med.end_date)  # it had no end date before the stop, and still has none
        self.assertEqual(list(response.context["medications"]), [self.med])
        self.assertContains(response, "Restarted metformin.")

    def test_restart_requires_post(self):
        self.assertEqual(self.client.get(self.url("medication_resume")).status_code, 405)

    def test_medication_past_its_end_date_is_in_past_list(self):
        ended = self.make_med(self.user, "amoxicillin", start_date=self.today - timedelta(days=10),
                              end_date=self.today - timedelta(days=1))
        ends_today = self.make_med(self.user, "ibuprofen", start_date=self.today - timedelta(days=2),
                                   end_date=self.today)
        response = self.client.get(reverse("home"))
        self.assertEqual(list(response.context["medications"]), [ends_today, self.med])
        self.assertEqual(list(response.context["past_medications"]), [ended])
        self.assertNotContains(response, self.url("medication_resume", ended))  # nothing to restart

    # --- delete ---
    def test_delete_asks_first_and_get_changes_nothing(self):
        response = self.client.get(self.url("medication_delete"))
        self.assertContains(response, "Delete metformin?")
        self.assertTrue(Medication.objects.filter(pk=self.med.pk).exists())

    def test_delete_removes_medication(self):
        response = self.client.post(self.url("medication_delete"), follow=True)
        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Deleted metformin.")
        self.assertFalse(Medication.objects.filter(pk=self.med.pk).exists())

    # --- access ---
    def test_other_users_medication_is_404_for_every_action(self):
        bobs = self.make_med(self.other, "warfarin")
        for name in ["medication_edit", "medication_stop", "medication_resume", "medication_delete"]:
            with self.subTest(name):
                self.assertEqual(self.client.post(self.url(name, bobs), VALID).status_code, 404)
                if name != "medication_resume":
                    self.assertEqual(self.client.get(self.url(name, bobs)).status_code, 404)
        bobs.refresh_from_db()
        self.assertEqual((bobs.name, bobs.discontinued_on), ("warfarin", None))

    def test_actions_require_login(self):
        self.client.logout()
        for name in ["medication_edit", "medication_stop", "medication_delete"]:
            with self.subTest(name):
                url = self.url(name)
                self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")
        self.client.post(self.url("medication_delete"))
        self.assertTrue(Medication.objects.filter(pk=self.med.pk).exists())

    def test_list_shows_edit_and_stop_links(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, self.url("medication_edit"))
        self.assertContains(response, self.url("medication_stop"))
