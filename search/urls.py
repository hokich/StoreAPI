from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    OftenSearchedProductsView,
    ProductsForYouView,
    SearchHintsView,
    SearchPageView,
    SearchQueriesView,
    SearchView,
)


router = DefaultRouter()

urlpatterns = [
    path("items/", SearchView.as_view(), name="search"),
    path("page/", SearchPageView.as_view(), name="search_page"),
    path("hints/", SearchHintsView.as_view(), name="hints"),
    path("query/", SearchQueriesView.as_view(), name="search-queries"),
    path("for-you/", ProductsForYouView.as_view(), name="for-you"),
    path(
        "often-search/",
        OftenSearchedProductsView.as_view(),
        name="often-search",
    ),
    path("", include(router.urls)),
]
