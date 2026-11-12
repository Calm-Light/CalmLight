import re
import uuid
from unittest import mock

from django.conf import settings
from django.test import Client, TestCase

from abtest.models import Click, Impression
from abtest.views import preferred_variant

PAGE = f"/{settings.ABTEST_HASH}/"
STATS = f"/{settings.ABTEST_HASH}/stats"
BUTTON = re.compile(r'<button[^>]*\bid="abtest"[^>]*>(.*?)</button>', re.S)


def button_texts(response):
    return [text.strip() for text in BUTTON.findall(response.content.decode())]


class AbtestRoutingTests(TestCase):
    def test_page_is_public(self):
        self.assertEqual(self.client.get(PAGE).status_code, 200)

    def test_stats_is_json(self):
        response = self.client.get(STATS)
        self.assertEqual(response.status_code, 200)
        self.assertIn("preferred", response.json())


class AbtestPageTests(TestCase):
    def test_lists_all_member_nicknames(self):
        response = self.client.get(PAGE)
        for nickname in settings.TEAM_MEMBERS:
            self.assertContains(response, nickname)

    def test_exactly_one_button_with_a_valid_variant(self):
        texts = button_texts(self.client.get(PAGE))
        self.assertEqual(len(texts), 1)
        self.assertIn(texts[0], ["kudos", "thanks"])

    def test_button_is_in_a_post_form(self):
        html = self.client.get(PAGE).content.decode()
        self.assertRegex(html, r'(?s)<form method="post"[^>]*>.*<button[^>]*id="abtest"')

    def test_variant_is_random_per_new_visitor(self):
        with mock.patch("abtest.views.random.choice", return_value="kudos"):
            self.assertEqual(button_texts(Client().get(PAGE)), ["kudos"])
        with mock.patch("abtest.views.random.choice", return_value="thanks"):
            self.assertEqual(button_texts(Client().get(PAGE)), ["thanks"])

    def test_both_variants_appear_across_many_visitors(self):
        seen = {button_texts(Client().get(PAGE))[0] for _ in range(40)}
        self.assertEqual(seen, {"kudos", "thanks"})

    def test_variant_is_sticky(self):
        first = button_texts(self.client.get(PAGE))
        for _ in range(5):
            self.assertEqual(button_texts(self.client.get(PAGE)), first)

    def test_reload_does_not_add_an_impression(self):
        for _ in range(3):
            self.client.get(PAGE)
        self.assertEqual(Impression.objects.count(), 1)

    def test_each_new_visitor_adds_one_impression(self):
        for _ in range(3):
            Client().get(PAGE)
        self.assertEqual(Impression.objects.count(), 3)

    def test_impression_stores_variant_and_timestamp(self):
        variant = button_texts(self.client.get(PAGE))[0]
        impression = Impression.objects.get()
        self.assertEqual(impression.variant, variant)
        self.assertIsNotNone(impression.created_at)


class AbtestClickTests(TestCase):
    def test_click_is_counted_with_visitor_variant(self):
        variant = button_texts(self.client.get(PAGE))[0]
        response = self.client.post(PAGE)
        self.assertRedirects(response, PAGE)
        click = Click.objects.get()
        self.assertEqual(click.variant, variant)
        self.assertIsNotNone(click.created_at)

    def test_double_click_counts_once(self):
        self.client.get(PAGE)
        self.client.post(PAGE)
        self.client.post(PAGE)
        self.assertEqual(Click.objects.count(), 1)

    def test_redirect_after_click_does_not_add_impression_or_change_variant(self):
        before = button_texts(self.client.get(PAGE))
        response = self.client.post(PAGE, follow=True)
        self.assertEqual(button_texts(response), before)
        self.assertEqual(Impression.objects.count(), 1)

    def test_click_without_seeing_page_is_not_counted(self):
        self.client.post(PAGE)
        self.assertEqual(Click.objects.count(), 0)

    def test_click_works_with_csrf_checks_on(self):
        browser = Client(enforce_csrf_checks=True)
        response = browser.get(PAGE)
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode()).group(1)
        browser.post(PAGE, {"csrfmiddlewaretoken": token})
        self.assertEqual(Click.objects.count(), 1)


class AbtestStatsTests(TestCase):
    def make(self, variant, impressions, clicks):
        visitors = [uuid.uuid4() for _ in range(impressions)]
        Impression.objects.bulk_create(Impression(visitor=v, variant=variant) for v in visitors)
        Click.objects.bulk_create(Click(visitor=v, variant=variant) for v in visitors[:clicks])

    def test_preferred_is_higher_click_rate_not_more_clicks(self):
        self.make("kudos", impressions=100, clicks=30)  # 30%
        self.make("thanks", impressions=10, clicks=5)  # 50%
        data = self.client.get(STATS).json()
        self.assertEqual(data["preferred"], "thanks")
        self.assertEqual(data["kudos"], {"impressions": 100, "clicks": 30, "rate": 0.3})
        self.assertEqual(data["thanks"], {"impressions": 10, "clicks": 5, "rate": 0.5})

    def test_preferred_kudos(self):
        self.make("kudos", impressions=212, clicks=63)
        self.make("thanks", impressions=207, clicks=21)
        self.assertEqual(self.client.get(STATS).json()["preferred"], "kudos")

    def test_empty_database_does_not_divide_by_zero(self):
        data = self.client.get(STATS).json()
        self.assertIn(data["preferred"], ["kudos", "thanks"])
        self.assertEqual(data["kudos"]["rate"], 0)

    def test_variant_with_zero_impressions(self):
        self.make("thanks", impressions=5, clicks=1)
        data = self.client.get(STATS).json()
        self.assertEqual(data["preferred"], "thanks")
        self.assertEqual(data["kudos"], {"impressions": 0, "clicks": 0, "rate": 0})

    def test_stats_are_live(self):
        self.assertEqual(self.client.get(STATS).json()["kudos"]["impressions"], 0)
        with mock.patch("abtest.views.random.choice", return_value="kudos"):
            self.client.get(PAGE)
        self.assertEqual(self.client.get(STATS).json()["kudos"]["impressions"], 1)

    def test_tie_breaks_on_clicks(self):
        results = {
            "kudos": {"rate": 0.5, "clicks": 1},
            "thanks": {"rate": 0.5, "clicks": 4},
        }
        self.assertEqual(preferred_variant(results), "thanks")
