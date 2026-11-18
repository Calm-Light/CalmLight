from django.urls import path

from meds import views

urlpatterns = [
    path("", views.home, name="home"),
    path("medications/add/", views.medication_add, name="medication_add"),
    path("medications/add/fill/", views.medication_fill, name="medication_fill"),
    path("medications/<int:pk>/edit/", views.medication_edit, name="medication_edit"),
    path("medications/<int:pk>/stop/", views.medication_stop, name="medication_stop"),
    path("medications/<int:pk>/restart/", views.medication_resume, name="medication_resume"),
    path("medications/<int:pk>/delete/", views.medication_delete, name="medication_delete"),
]
