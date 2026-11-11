from unittest import mock

from django.test import SimpleTestCase, override_settings

from meds import ai


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
