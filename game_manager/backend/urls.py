from django.urls import include, path
from rest_framework import routers

from . import views

# router = routers.DefaultRouter()
# router.register(r'users', views.UserViewSet)
# router.register(r'groups', views.GroupViewSet)
# router.register(r'companies', views.CompanyList.as_view())

urlpatterns = [
    path("", views.index, name="index"),
    path("images/<str:image_id>", views.serveImage, name="images"),
    # path("api/companies", views.CompanyList.as_view()),
    path("api/companies/<str:uuid>", views.CompanyDetail.as_view()),
    # path("api/genres", views.GenreList.as_view()),
    # path("api/platforms", views.PlatformList.as_view()),
    path("api/platforms/<str:url_slug>", views.PlatformDetailList.as_view()),
    path("api/franchises/<str:url_slug>", views.FranchiseDetail.as_view()),
    # path("api/modes", views.ModeList.as_view()),
    path("api/games", views.GameList.as_view()),
    path("api/games/", views.GameList.as_view()),
    path("api/games/<str:url_slug>/", views.GameDetailList.as_view(), name='game-detail'),
    path("api/games/<str:url_slug>/releases", views.GameRelease.as_view({'get': 'list'})),
    # path("api/games/<str:url_slug>/reviews", views.GameRelease.as_view({'get': 'list'})),
    path("api/games/<str:url_slug>/purchases", views.GamePurchase.as_view({'get': 'list'})),
    # path("api/releases", views.ReleaseList.as_view()),
    path("healthz", views.healthcheck, name="healthz")
]