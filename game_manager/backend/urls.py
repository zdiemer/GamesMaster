from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("healthz", views.healthcheck, name="healthz")
]