from unittest import mock

from django.db import OperationalError
from django.test import TestCase


class HealthzTests(TestCase):
    def test_ok_when_database_answers(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_503_when_database_is_down(self):
        with mock.patch("config.views.connection.cursor", side_effect=OperationalError("down")):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "error")

    def test_public_without_login(self):
        self.assertNotIn("/login/", self.client.get("/healthz").get("Location", ""))
