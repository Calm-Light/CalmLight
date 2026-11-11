from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    # Sprint 2: replace with today's dose checklist.
    return render(request, "meds/home.html")
