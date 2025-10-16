from django.utils import timezone

from utils.exceptions import (
    ProductIsNotInStockException,
    ProductIsNotPublishedException,
)

from ..models import Product, ProductDay


def create_product_day(product_id: int, dt: timezone.datetime) -> ProductDay:
    """Creates a Product of the Day entry."""
    product = Product.get_product_by_pk(product_id)

    if not product.publish:
        raise ProductIsNotPublishedException(
            {"message": f"Product with pk '{product_id}' is not published."}
        )

    if not product.quantity:
        raise ProductIsNotInStockException(
            {"message": f"Product with pk '{product_id}' is not in stock."}
        )

    product_day = ProductDay.objects.create(
        product=product,
        show_date=dt.date(),
    )
    return product_day


PRODUCT_DAY_CATEGORIES: list[str] = [
    "televizory",
    "noutbuki",
    "stiralnye-mashiny",
    "smartfony",
    "holodilniki",
    "morozilnye-lari",
    "morozilnye-kamery",
    "planshety",
    "gazovye-plity",
    "ehlektricheskie-plity",
    "kombinirovannye-plity",
    "vstraivaemye-duhovye-shkafy",
    "vstraivaemye-paneli",
    "vytyazhki",
    "posudomoechnye-mashiny",
    "mikrovolnovye-pechi",
    "multivarki",
    "ehlektropechi",
    "kuhonnye-kombajny",
    "myasorubki",
    "ehlektrochajniki",
    "akusticheskie-sistemy",
    "printery-i-mfu",
    "pylesosy",
    "kofemashiny",
    "kofevarki",
    "utyugi",
    "blendery",
    "feny",
    "ehlektrobritvy",
]


def set_products_day_today() -> None:
    """
    Sets Product of the Day entries for today.
    Select 10 products priced from 3000 with the highest stock
    """
    products = Product.objects.filter(
        publish=True,
        quantity__gte=1,  # >= 1,
        price__gte=3000,
        _tags__slug__in=PRODUCT_DAY_CATEGORIES,
    ).order_by("-quantity")[:10]

    ProductDay.clean_products_day()

    for product in products:
        create_product_day(product.id, timezone.now())
