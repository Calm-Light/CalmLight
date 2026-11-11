from django.urls import path

from meds import views

urlpatterns = [
    path("", views.home, name="home"),
]
