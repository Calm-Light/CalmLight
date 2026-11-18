from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class DoseUnit(models.TextChoices):
    MG = "mg", "mg"
    MCG = "mcg", "mcg"
    G = "g", "g"
    ML = "mL", "mL"
    UNITS = "units", "units"
    TABLET = "tablet", "tablet(s)"
    CAPSULE = "capsule", "capsule(s)"
    PUFF = "puff", "puff(s)"
    DROP = "drop", "drop(s)"


class Route(models.TextChoices):
    ORAL = "oral", "Oral"
    SUBCUTANEOUS = "subcutaneous", "Subcutaneous injection"
    TOPICAL = "topical", "Topical"
    TRANSDERMAL = "transdermal", "Transdermal patch"
    NASAL = "nasal", "Nasal spray"
    OTHER = "other", "Other"


class Frequency(models.IntegerChoices):
    ONCE = 1, "Once daily"
    TWICE = 2, "Twice daily"
    THREE = 3, "Three times daily"


class MealTiming(models.TextChoices):
    NONE = "none", "No meal instructions"
    BEFORE = "before", "Before meals"
    WITH = "with", "With meals"
    AFTER = "after", "After meals"


class Medication(models.Model):
    """One medication a user takes. Entered by the user; the app never prescribes."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField("Generic name", max_length=120)
    dose_amount = models.DecimalField(
        "Dose", max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    dose_unit = models.CharField("Unit", max_length=10, choices=DoseUnit.choices)
    route = models.CharField(max_length=20, choices=Route.choices, default=Route.ORAL)
    times_per_day = models.PositiveSmallIntegerField("How often", choices=Frequency.choices)
    meal_timing = models.CharField(
        "Meal instructions", max_length=10, choices=MealTiming.choices, default=MealTiming.NONE
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave empty if there is no end date.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=F("start_date")),
                name="medication_end_not_before_start",
            ),
            models.CheckConstraint(condition=Q(dose_amount__gt=0), name="medication_dose_positive"),
        ]

    def __str__(self):
        return f"{self.name} {self.dose}"

    @property
    def dose(self):
        """e.g. "500 mg" or "1.5 tablet(s)"."""
        if self.dose_amount is None:
            return ""
        return f"{self.dose_amount.normalize():f} {self.get_dose_unit_display()}"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be earlier than the start date."})


class AIRequest(models.Model):
    """One call to the LLM, used for the per-user daily limit."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_requests")
    feature = models.CharField(max_length=30)
    succeeded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.feature} by {self.user} at {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def used_today(cls, user):
        from django.utils import timezone

        start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        return cls.objects.filter(user=user, created_at__gte=start).count()
