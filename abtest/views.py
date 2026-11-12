"""
Public A/B test page at /<hash>/ and live results at /<hash>/stats.

Each visitor gets "kudos" or "thanks" at random (50/50), kept in their session.
GET  /<hash>/       counts one impression per visitor (reloads and redirects do not add more).
POST /<hash>/       counts at most one click per visitor, then redirects back to the page.
GET  /<hash>/stats  JSON with the variant that has the higher click rate, computed live.
"""

import random
import uuid

from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from abtest.models import Click, Impression, Variant

SESSION_VISITOR = "abtest_visitor"
SESSION_VARIANT = "abtest_variant"
VARIANTS = [Variant.KUDOS.value, Variant.THANKS.value]


def _visitor(request):
    """Return (visitor_id, variant) for this visitor, assigning a random variant on first visit."""
    variant = request.session.get(SESSION_VARIANT)
    visitor = request.session.get(SESSION_VISITOR)
    if variant not in VARIANTS or not visitor:
        variant = random.choice(VARIANTS)
        visitor = str(uuid.uuid4())
        request.session[SESSION_VARIANT] = variant
        request.session[SESSION_VISITOR] = visitor
    return visitor, variant


@never_cache
def page(request):
    visitor, variant = _visitor(request)
    if request.method == "POST":
        # Only count a click from someone who was shown the page (has an impression).
        if Impression.objects.filter(visitor=visitor).exists():
            Click.objects.get_or_create(visitor=visitor, defaults={"variant": variant})
        return redirect("abtest:page")
    Impression.objects.get_or_create(visitor=visitor, defaults={"variant": variant})
    return render(request, "abtest/page.html", {"members": settings.TEAM_MEMBERS, "variant": variant})


def _counts(model):
    rows = model.objects.values("variant").annotate(n=Count("id"))
    counts = {v: 0 for v in VARIANTS}
    counts.update({row["variant"]: row["n"] for row in rows if row["variant"] in counts})
    return counts


def preferred_variant(results):
    """The variant with the higher click rate; ties go to the one with more clicks, then kudos."""
    return max(VARIANTS, key=lambda v: (results[v]["rate"], results[v]["clicks"], v == Variant.KUDOS))


@never_cache
def stats(request):
    impressions, clicks = _counts(Impression), _counts(Click)
    results = {}
    for v in VARIANTS:
        rate = clicks[v] / impressions[v] if impressions[v] else 0.0
        results[v] = {"impressions": impressions[v], "clicks": clicks[v], "rate": round(rate, 4)}
    return JsonResponse({"preferred": preferred_variant(results), **results})
