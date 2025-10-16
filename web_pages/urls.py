from django.urls import path

from .views import GetSimplePageView


urlpatterns = [
    path("<slug:slug>/", GetSimplePageView.as_view(), name="simple-page"),
]
