from django.urls import path

from meds import views

urlpatterns = [
    path("", views.home, name="home"),
    path("medications/add/", views.medication_add, name="medication_add"),
]
