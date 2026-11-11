"""
The only place MedTrack talks to an LLM.

Rules:
- Called from the server only, never from browser JavaScript.
- Tests must mock `call_openrouter` (or `weekly_summary`); they never hit the network.
- Never send names or emails to the LLM; send dose data only.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_SECONDS = 30


class AIUnavailable(Exception):
    """Raised when the LLM cannot be reached or returns an unusable answer."""


def call_openrouter(messages, response_format=None):
    """Send chat messages to OpenRouter and return the assistant's text."""
    if not settings.OPENROUTER_API_KEY or not settings.OPENROUTER_MODEL:
        raise AIUnavailable("OPENROUTER_API_KEY and OPENROUTER_MODEL must be set.")
    payload = {"model": settings.OPENROUTER_MODEL, "messages": messages}
    if response_format:
        payload["response_format"] = response_format
    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        logger.warning("OpenRouter call failed: %s", exc)
        raise AIUnavailable(str(exc)) from exc


def weekly_summary(user, week_start):
    """
    Return a dict summarising one user's adherence for the week starting `week_start`.

    Planned shape (finalise in the AI-summary issue):
        {"summary": str, "missed_patterns": [{"medication": str, "pattern": str}]}
    """
    raise NotImplementedError("Weekly summary is planned for a later sprint.")
