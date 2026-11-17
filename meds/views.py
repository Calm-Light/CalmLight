from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from meds import ai
from meds.forms import LabelTextForm, MedicationForm
from meds.models import AIRequest


@login_required
def home(request):
    """The user's own medication list. (Today's dose checklist comes in a later sprint.)"""
    medications = request.user.medications.all()
    return render(request, "meds/home.html", {"medications": medications})


def _render_add(request, form, label_form=None, **extra):
    context = {
        "form": form,
        "label_form": label_form or LabelTextForm(),
        "ai_left": max(settings.AI_DAILY_LIMIT - AIRequest.used_today(request.user), 0),
        **extra,
    }
    return render(request, "meds/medication_form.html", context)


@login_required
def medication_add(request):
    form = MedicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        medication = form.save(commit=False)
        medication.user = request.user
        medication.save()
        messages.success(request, f"Added {medication.name}.")
        return redirect("home")
    return _render_add(request, form)


@login_required
@require_POST
def medication_fill(request):
    """Smart add: the AI reads pasted label text and pre-fills the form. Nothing is saved here."""
    label_form = LabelTextForm(request.POST)
    if not label_form.is_valid():
        return _render_add(request, MedicationForm(), label_form)

    if AIRequest.used_today(request.user) >= settings.AI_DAILY_LIMIT:
        messages.error(request, "You've reached today's limit for AI fill. Please fill in the form yourself.")
        return _render_add(request, MedicationForm(), label_form)

    usage = AIRequest.objects.create(user=request.user, feature="smart_add")
    try:
        fields, missing = ai.parse_label(label_form.cleaned_data["label_text"])
    except ai.AIUnavailable:
        messages.error(request, "AI fill isn't available right now. Please fill in the form yourself.")
        return _render_add(request, MedicationForm(), label_form)
    usage.succeeded = True
    usage.save(update_fields=["succeeded"])

    if not fields:
        messages.warning(request, "The AI couldn't find medication details in that text. Please fill in the form yourself.")
        return _render_add(request, MedicationForm(), label_form)

    messages.info(request, "The AI filled in the form. Check every field before you save. It can make mistakes.")
    return _render_add(request, MedicationForm(initial=fields), label_form, ai_missing=missing, ai_filled=True)
