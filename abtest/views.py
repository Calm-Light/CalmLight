"""
A/B test page. OWNER: see the A/B test issue for the full spec.

Placeholder only: the URLs are wired up (/<hash>/ and /<hash>/stats) so the
real implementation can replace these two functions without touching routing.
"""

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render


def page(request):
    # TODO(A/B issue): assign variant per visitor, count impression once, render button.
    return render(request, "abtest/page.html", {"members": settings.TEAM_MEMBERS, "variant": None})


def stats(request):
    # TODO(A/B issue): compute preferred variant live from the database.
    return JsonResponse({"preferred": None})
