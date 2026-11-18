from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

SEED_ENV = {"SEED_ADMIN_PASSWORD": "test-admin-pw-123", "SEED_MEMBER_PASSWORD": "test-member-pw-123"}


class SeedCommandTests(TestCase):
    @mock.patch.dict("os.environ", SEED_ENV)
    def test_seed_is_idempotent(self):
        call_command("seed", stdout=mock.MagicMock())
        call_command("seed", stdout=mock.MagicMock())
        User = get_user_model()
        self.assertEqual(User.objects.count(), 2)
        admin = User.objects.get(username="admin@example.com")
        self.assertTrue(admin.is_superuser and admin.is_staff)
        member = User.objects.get(username="member@example.com")
        self.assertFalse(member.is_staff)
        self.assertTrue(member.check_password("test-member-pw-123"))

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_seed_requires_passwords(self):
        with self.assertRaises(CommandError):
            call_command("seed", stdout=mock.MagicMock())


class AuthFlowTests(TestCase):
    def test_login_page_loads(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_signup_logs_user_in(self):
        response = self.client.post(
            reverse("signup"),
            {"email": "newuser@example.com", "password1": "a-long-pass-987", "password2": "a-long-pass-987"},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(get_user_model().objects.filter(username="newuser@example.com").exists())

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_logout_is_post(self):
        get_user_model().objects.create_user("u", password="a-long-pass-987")
        self.client.login(username="u", password="a-long-pass-987")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))


class VisibleFeedbackTests(TestCase):
    """Users must see what happened after submitting a form."""

    def test_wrong_password_shows_red_alert(self):
        response = self.client.post(reverse("login"), {"username": "nobody", "password": "wrong"})
        self.assertContains(response, 'class="alert alert-danger"')
        self.assertContains(response, "Please enter a correct email")

    def test_weak_signup_password_marks_field_invalid(self):
        response = self.client.post(
            reverse("signup"), {"email": "weak@example.com", "password1": "123", "password2": "123"}
        )
        self.assertContains(response, 'class="alert alert-danger"')
        self.assertContains(response, "is-invalid")
        self.assertContains(response, "invalid-feedback")

    def test_login_shows_welcome_message(self):
        get_user_model().objects.create_user("u", password="a-long-pass-987")
        response = self.client.post(
            reverse("login"), {"username": "u", "password": "a-long-pass-987"}, follow=True
        )
        self.assertContains(response, "Logged in as u.")

    def test_signup_shows_welcome_message(self):
        response = self.client.post(
            reverse("signup"),
            {"email": "fresh@example.com", "password1": "a-long-pass-987", "password2": "a-long-pass-987"},
            follow=True,
        )
        self.assertContains(response, "Account created. Welcome, fresh@example.com!")
        self.assertNotContains(response, "Logged in as")

    def test_logout_shows_message(self):
        get_user_model().objects.create_user("u", password="a-long-pass-987")
        self.client.login(username="u", password="a-long-pass-987")
        response = self.client.post(reverse("logout"), follow=True)
        self.assertContains(response, "You have been logged out.")


class EmailSignupTests(TestCase):
    """Issue #9: register with an email address and password."""

    def signup(self, email="Pat@Example.com ", password="a-long-pass-987", **extra):
        data = {"email": email, "password1": password, "password2": password, **extra}
        return self.client.post(reverse("signup"), data)

    def test_signup_page_asks_for_email_not_username(self):
        response = self.client.get(reverse("signup"))
        self.assertContains(response, 'type="email"')
        self.assertContains(response, 'name="email"')
        self.assertNotContains(response, 'name="username"')

    def test_email_becomes_lower_case_username_and_password_is_hashed(self):
        self.assertRedirects(self.signup(), reverse("home"))
        user = get_user_model().objects.get()
        self.assertEqual((user.username, user.email), ("pat@example.com", "pat@example.com"))
        self.assertNotEqual(user.password, "a-long-pass-987")
        self.assertTrue(user.check_password("a-long-pass-987"))
        self.assertFalse(user.is_staff)

    def test_email_is_required_and_must_be_valid(self):
        for email, error in [("", "This field is required."), ("not-an-email", "Enter a valid email address.")]:
            with self.subTest(email=email):
                response = self.signup(email=email)
                self.assertContains(response, error)
                self.assertContains(response, "is-invalid")
        self.assertFalse(get_user_model().objects.exists())

    def test_duplicate_email_is_rejected_ignoring_case(self):
        get_user_model().objects.create_user("member@example.com", "member@example.com", "a-long-pass-987")
        response = self.signup(email="MEMBER@example.com")
        self.assertContains(response, "An account with this email already exists.")
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_password_needs_8_characters_and_must_match(self):
        self.assertContains(self.signup(password="short1x"), "at least 8 characters")
        response = self.client.post(reverse("signup"), {"email": "a@example.com", "password1": "a-long-pass-987",
                                                        "password2": "a-long-pass-988"})
        self.assertContains(response, "didn")  # "The two password fields didn't match."
        self.assertFalse(get_user_model().objects.exists())

    def test_password_too_similar_to_email_is_rejected(self):
        self.assertContains(self.signup(email="sunflower7@example.com", password="sunflower7"), "too similar")

    def test_login_with_email_in_any_case(self):
        self.signup()
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": " PAT@example.com", "password": "a-long-pass-987"})
        self.assertRedirects(response, reverse("home"))

    def test_seeded_accounts_still_log_in(self):
        get_user_model().objects.create_user("member@example.com", "member@example.com", "a-long-pass-987")
        response = self.client.post(reverse("login"), {"username": "member@example.com", "password": "a-long-pass-987"})
        self.assertRedirects(response, reverse("home"))


class ErrorPageTests(TestCase):
    def test_404_page_uses_site_layout(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, "MedTrack", status_code=404)

    def test_500_page_renders_without_context(self):
        from django.template.loader import render_to_string

        self.assertIn("Something went wrong", render_to_string("500.html"))
