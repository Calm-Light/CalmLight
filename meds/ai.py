"""
The only place MedTrack talks to an LLM.

Rules:
- Called from the server only, never from browser JavaScript.
- Tests must mock `call_openrouter`; they never hit the network.
- Never send the user's name or email to the LLM. Smart add sends only the label text the user pasted.
- The LLM output never goes straight into the database: `clean_label_fields` keeps only valid values,
  and the user reviews the filled-in form before saving.
"""

import json
import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

from meds.models import DoseUnit, Frequency, MealTiming, Route

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_SECONDS = 30
MAX_LABEL_CHARS = 1000


class AIUnavailable(Exception):
    """Raised when the LLM cannot be reached or returns an unusable answer."""


def call_openrouter(messages, response_format=None):
    """Send chat messages to OpenRouter and return the assistant's text."""
    if not settings.OPENROUTER_API_KEY or not settings.OPENROUTER_MODEL:
        raise AIUnavailable("OPENROUTER_API_KEY and OPENROUTER_MODEL must be set.")
    payload = {"model": settings.OPENROUTER_MODEL, "messages": messages, "temperature": 0}
    if response_format:
        payload["response_format"] = response_format
        # Only route to providers that support structured output.
        payload["provider"] = {"require_parameters": True}
    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if not content:
            raise ValueError("empty response")
        return content
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("OpenRouter call failed: %s", exc)
        raise AIUnavailable(str(exc)) from exc


# --- Smart add: prescription label text -> medication form fields ----------------

LABEL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": ["string", "null"], "description": "Generic medication name, lowercase."},
        "dose_amount": {"type": ["number", "null"], "description": "Amount per dose, e.g. 500."},
        "dose_unit": {"type": ["string", "null"], "enum": [*DoseUnit.values, None]},
        "route": {"type": ["string", "null"], "enum": [*Route.values, None]},
        "times_per_day": {"type": ["integer", "null"], "enum": [*Frequency.values, None]},
        "meal_timing": {"type": ["string", "null"], "enum": [*MealTiming.values, None]},
    },
    "required": ["name", "dose_amount", "dose_unit", "route", "times_per_day", "meal_timing"],
    "additionalProperties": False,
}

LABEL_PROMPT = """You read prescription labels and fill in a medication form.
Use only what the text says. If a value is not stated or you are unsure, use null. Never guess a dose.
- name: the generic name (if only a brand name is given, use the brand name), lowercase.
- dose_amount and dose_unit: the amount taken each time, e.g. "take 2 tablets" -> 2, "tablet";
  "500 mg tablet, take 1" -> 500, "mg". Sprays and inhaler puffs -> "puff"; eye, ear or nose drops -> "drop";
  insulin -> "units". Use "tablet" or "capsule" only for things that are swallowed.
- route: "oral" for anything swallowed or taken by mouth ("by mouth", "PO", "swallow", tablets and capsules
  with no other route); "subcutaneous" for injections under the skin; "topical" for creams or ointments applied
  to the skin; "transdermal" for patches; "nasal" for sprays in the nose; "other" for any other stated route.
- times_per_day: 1, 2 or 3 ("every 12 hours" = 2, "every 8 hours" = 3). Use null for other schedules or "as needed".
- meal_timing: "before", "with" or "after" meals, or "none" if the label gives no meal instruction.
Reply with JSON only."""

FIELD_LABELS = {
    "name": "name",
    "dose_amount": "dose",
    "dose_unit": "unit",
    "route": "route",
    "times_per_day": "how often",
    "meal_timing": "meal instructions",
}

# These form fields have a default (Oral, No meal instructions), so a missing value shows the default
# and the user is asked to check it rather than fill it in.
FIELDS_WITH_DEFAULT = {FIELD_LABELS["route"], FIELD_LABELS["meal_timing"]}


def clean_label_fields(data):
    """
    Keep only values the medication form accepts. Returns (fields, missing).
    `fields` can be used as the form's initial data; `missing` lists what the user must fill in.
    """
    data = data if isinstance(data, dict) else {}
    fields = {}

    name = data.get("name")
    if isinstance(name, str) and name.strip():
        fields["name"] = " ".join(name.split())[:120]

    amount = data.get("dose_amount")
    if not isinstance(amount, bool) and isinstance(amount, (int, float, str)):
        try:
            value = Decimal(str(amount))
            if value.is_finite() and Decimal("0") < value < Decimal("1000000"):
                value = value.quantize(Decimal("0.01")).normalize()
                # normalize() turns 500 into 5E+2; keep whole numbers as plain digits for the form.
                if value == value.to_integral_value():
                    value = value.quantize(Decimal("1"))
                fields["dose_amount"] = value
        except InvalidOperation:
            pass

    for key, allowed in (("dose_unit", DoseUnit.values), ("route", Route.values), ("meal_timing", MealTiming.values)):
        if data.get(key) in allowed:
            fields[key] = data[key]

    times = data.get("times_per_day")
    if not isinstance(times, bool) and times in Frequency.values:
        fields["times_per_day"] = times

    missing = [FIELD_LABELS[key] for key in FIELD_LABELS if key not in fields]
    return fields, missing


def parse_label(text):
    """Ask the LLM to read label text. Returns (fields, missing). Raises AIUnavailable."""
    content = call_openrouter(
        [
            {"role": "system", "content": LABEL_PROMPT},
            {"role": "user", "content": text[:MAX_LABEL_CHARS]},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "medication_label", "strict": True, "schema": LABEL_SCHEMA},
        },
    )
    try:
        data = json.loads(content.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
    except json.JSONDecodeError as exc:
        logger.warning("Smart add: model returned non-JSON output")
        raise AIUnavailable("The AI reply was not valid JSON.") from exc
    return clean_label_fields(data)
