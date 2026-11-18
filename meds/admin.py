from django.contrib import admin

from meds.models import AIRequest, Medication


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "dose", "times_per_day", "user", "start_date", "end_date")
    list_filter = ("route", "times_per_day")
    search_fields = ("name", "user__username")


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ("feature", "user", "succeeded", "created_at")
    list_filter = ("feature", "succeeded")
    readonly_fields = ("user", "feature", "succeeded", "created_at")
