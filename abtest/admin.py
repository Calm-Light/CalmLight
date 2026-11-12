from django.contrib import admin

from abtest.models import Click, Impression


# Before the bot run, delete test visits here: select all rows, then "Delete selected".
@admin.register(Impression)
class ImpressionAdmin(admin.ModelAdmin):
    list_display = ("variant", "created_at", "visitor")
    list_filter = ("variant",)
    date_hierarchy = "created_at"
    readonly_fields = ("visitor", "variant", "created_at")


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ("variant", "created_at", "visitor")
    list_filter = ("variant",)
    date_hierarchy = "created_at"
    readonly_fields = ("visitor", "variant", "created_at")
