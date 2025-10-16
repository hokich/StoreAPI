from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.cart import CartViewSet
from .views.compare import CompareViewSet
from .views.customer import CustomerViewSet
from .views.favorites import FavoritesViewSet
from .views.orders import CreateNewOrderViewSet
from .views.product_reviews import CreateProductReviewView
from .views.recently_viewed import RecentlyViewedViewSet


router = DefaultRouter()

router.register(
    r"",
    CustomerViewSet,
    basename="customer",
)

router.register(
    r"recently-viewed",
    RecentlyViewedViewSet,
    basename="recently-viewed",
)

router.register(
    r"cart",
    CartViewSet,
    basename="cart",
)

router.register(
    r"favorites",
    FavoritesViewSet,
    basename="favorites",
)

router.register(
    r"compare",
    CompareViewSet,
    basename="compare",
)

router.register(
    r"order/new",
    CreateNewOrderViewSet,
    basename="new-order",
)

urlpatterns = [
    path("", include(router.urls)),
    path("create-review/", CreateProductReviewView.as_view()),
]
