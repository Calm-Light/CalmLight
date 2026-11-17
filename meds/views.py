from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from meds.forms import MedicationForm


@login_required
def home(request):
    """The user's own medication list. (Today's dose checklist comes in a later sprint.)"""
    medications = request.user.medications.all()
    return render(request, "meds/home.html", {"medications": medications})


@login_required
def medication_add(request):
    form = MedicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        medication = form.save(commit=False)
        medication.user = request.user
        medication.save()
        messages.success(request, f"Added {medication.name}.")
        return redirect("home")
    return render(request, "meds/medication_form.html", {"form": form})
