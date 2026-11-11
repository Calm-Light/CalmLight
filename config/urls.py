from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from config import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", views.healthz, name="healthz"),
    # /login/, /logout/, /signup/
    path("", include("accounts.urls")),
    # Public A/B test page: /<hash>/ and /<hash>/stats
    path(f"{settings.ABTEST_HASH}/", include("abtest.urls")),
    # MedTrack features (home page = today's doses)
    path("", include("meds.urls")),
]
