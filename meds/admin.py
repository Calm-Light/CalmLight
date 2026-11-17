from django.contrib import admin

from meds.models import Medication


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "dose", "times_per_day", "user", "start_date", "end_date")
    list_filter = ("route", "times_per_day")
    search_fields = ("name", "user__username")
