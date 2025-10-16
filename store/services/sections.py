import datetime

from django.utils import timezone

from ..models import FreeTag, Product, Selection


DISPLAY_CATEGORIES_SECTIONS: list[str] = [
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
    "skovorodki",
    "nabory-posudy",
    "kastryuli",
]


def update_bestsellers_products() -> None:
    """Updates the list of best-selling products and assigns the 'hit' tag."""
    bestseller_tag = FreeTag.get_object_by_slug("hit")
    products = Product.objects.filter(publish=True)
    for product in products:
        product.sales.update_index()
        product._tags.remove(bestseller_tag)

    bestsellers_products = (
        Product.objects.filter(
            publish=True,
            quantity__gte=1,  # >= 1
            _tags__slug__in=DISPLAY_CATEGORIES_SECTIONS,
        )
        .exclude(sales___index=0)
        .order_by("-sales___index")[:100]
    )
    for bs_product in bestsellers_products:
        bs_product._tags.add(bestseller_tag)


def update_best_prices_products() -> None:
    """Updates products with the best discount and assigns the 'best price' tag."""
    best_price_tag = FreeTag.get_object_by_slug("luchshaya-cena")
    for product in Product.objects.filter(publish=True):
        product._tags.remove(best_price_tag)

    best_prices_products = Product.objects.filter(
        publish=True,
        quantity__gte=1,  # >= 1
        _tags__slug__in=DISPLAY_CATEGORIES_SECTIONS,
        discount_percent__gt=0,
    ).order_by("-discount_percent")[:100]

    for product in best_prices_products:
        product._tags.add(best_price_tag)


def set_promo_tag() -> None:
    """Assigns the 'promo' tag to all discounted products."""
    promo_tag = Selection.get_object_by_slug("akcionnye-tovary")
    for prod in Product.objects.filter(publish=True):
        prod._tags.remove(promo_tag)
    for product in Product.objects.exclude(discount_percent=0):
        product._tags.add(promo_tag)


def remove_new_arrival_tag() -> None:
    """Removes the 'new arrival' tag from products older than 29 days."""
    new_product_tag = FreeTag.get_object_by_slug("novinka")
    exp_date = timezone.now() - datetime.timedelta(days=29)
    for product in Product.objects.filter(
        _tags=new_product_tag, created_at__lte=exp_date
    ):
        product._tags.remove(new_product_tag)
