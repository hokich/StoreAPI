from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.catalog import (
    CatalogTreeViewSet,
    CatalogViewSet,
    FavoriteBrandsViewSet,
)
from .views.city import CitiesListViewSet
from .views.product import ProductViewSet
from .views.product_day import ProductsDayViewSet
from .views.sections import ProductsSectionsViewSet
from .views.shops import ShopsListViewSet
from .views.sitemap import SitemapDataAPIView


router = DefaultRouter()

router.register(
    r"products-day",
    ProductsDayViewSet,
    basename="products-day",
)

router.register(
    r"section",
    ProductsSectionsViewSet,
    basename="products-section",
)

router.register(
    r"catalog/tree",
    CatalogTreeViewSet,
    basename="catalog-tree",
)

router.register(
    r"catalog/favorite-brands",
    FavoriteBrandsViewSet,
    basename="catalog-favorite-brands",
)

router.register(
    r"catalog",
    CatalogViewSet,
    basename="catalog",
)

router.register(r"shops", ShopsListViewSet, basename="shops")
router.register(r"cities", CitiesListViewSet, basename="cities")
router.register(r"product", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
    path("sitemap-data/", SitemapDataAPIView.as_view(), name="sitemap-data"),
]
