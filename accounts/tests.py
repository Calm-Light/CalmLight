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
            {"username": "newuser", "password1": "a-long-pass-987", "password2": "a-long-pass-987"},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())

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
        self.assertContains(response, "Please enter a correct username")

    def test_weak_signup_password_marks_field_invalid(self):
        response = self.client.post(
            reverse("signup"), {"username": "weak", "password1": "123", "password2": "123"}
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
            {"username": "fresh", "password1": "a-long-pass-987", "password2": "a-long-pass-987"},
            follow=True,
        )
        self.assertContains(response, "Account created. Welcome, fresh!")
        self.assertNotContains(response, "Logged in as")

    def test_logout_shows_message(self):
        get_user_model().objects.create_user("u", password="a-long-pass-987")
        self.client.login(username="u", password="a-long-pass-987")
        response = self.client.post(reverse("logout"), follow=True)
        self.assertContains(response, "You have been logged out.")
