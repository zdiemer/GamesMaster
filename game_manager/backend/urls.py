from django.urls import include, path
from rest_framework import routers

from . import views

# router = routers.DefaultRouter()
# router.register(r'users', views.UserViewSet)
# router.register(r'groups', views.GroupViewSet)
# router.register(r'companies', views.CompanyList.as_view())

urlpatterns = [
    path("", views.index, name="index"),
    path("api/companies", views.CompanyList.as_view()),
    path("api/genres", views.GenreList.as_view()),
    path("api/platforms", views.PlatformList.as_view()),
    path("api/modes", views.ModeList.as_view()),
    path("api/games", views.GameList.as_view()),
    path("api/games/", views.GameList.as_view()),
    path("api/games/<int:pk>/", views.GameDetailList.as_view(), name='game-detail'),
    path("api/games/<int:pk>/releases", views.GameRelease.as_view({'get': 'list'})),
    path("api/releases", views.ReleaseList.as_view()),
    path("healthz", views.healthcheck, name="healthz")
]