from django.db import models


class Variant(models.TextChoices):
    KUDOS = "kudos", "kudos"
    THANKS = "thanks", "thanks"


class Impression(models.Model):
    """One row per visitor: the first time they saw the A/B page."""

    # Random id kept in the visitor's session. Unique, so a visitor can only be counted once.
    visitor = models.UUIDField(unique=True)
    variant = models.CharField(max_length=6, choices=Variant.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.variant} impression at {self.created_at:%Y-%m-%d %H:%M}"


class Click(models.Model):
    """One row per visitor who clicked the button. Unique, so double clicks count once."""

    visitor = models.UUIDField(unique=True)
    variant = models.CharField(max_length=6, choices=Variant.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.variant} click at {self.created_at:%Y-%m-%d %H:%M}"
