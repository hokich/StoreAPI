from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ShortLinkViewSet


router = DefaultRouter()

router.register(
    r"",
    ShortLinkViewSet,
    basename="short-link",
)


urlpatterns = [
    path("", include(router.urls)),
]
