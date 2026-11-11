from django.urls import path

from abtest import views

app_name = "abtest"

urlpatterns = [
    path("", views.page, name="page"),
    path("stats", views.stats, name="stats"),
]
