from django.conf import settings
from django.test import TestCase


class AbtestRoutingTests(TestCase):
    """Routing only. The A/B owner adds counting tests here."""

    def test_page_is_public(self):
        self.assertEqual(self.client.get(f"/{settings.ABTEST_HASH}/").status_code, 200)

    def test_stats_is_json(self):
        response = self.client.get(f"/{settings.ABTEST_HASH}/stats")
        self.assertEqual(response.status_code, 200)
        self.assertIn("preferred", response.json())
