from django import forms
from django.utils import timezone

from accounts.forms import BootstrapMixin
from meds.models import Medication


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d", **kwargs)


class MedicationForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Medication
        fields = [
            "name",
            "dose_amount",
            "dose_unit",
            "route",
            "times_per_day",
            "meal_timing",
            "start_date",
            "end_date",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. metformin", "autocomplete": "off"}),
            "dose_amount": forms.NumberInput(attrs={"step": "any", "min": "0", "inputmode": "decimal"}),
            "start_date": DateInput(),
            "end_date": DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault("start_date", timezone.localdate())
        # Required selects start blank so the user must choose; give the blank option a clear label.
        for name, prompt in (("dose_unit", "Choose a unit"), ("times_per_day", "Choose how often")):
            choices = [c for c in self.fields[name].choices if c[0] != ""]
            self.fields[name].choices = [("", prompt), *choices]

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())
