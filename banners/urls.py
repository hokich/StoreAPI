from django.urls import path

from .views import GetActiveBannersView


urlpatterns = [
    path("list/", GetActiveBannersView.as_view(), name="active-banners"),
]
