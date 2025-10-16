from store.services.product_day import set_products_day_today
from store.services.sections import (
    remove_new_arrival_tag,
    set_promo_tag,
    update_best_prices_products,
)


def run() -> None:
    """Daily scheduled task for updating store product tags and featured products."""
    # Create today's "Products of the Day"
    set_products_day_today()
    # Assign "Promo" tags
    set_promo_tag()
    # Assign "Best Price" tags to products with the highest discounts
    update_best_prices_products()
    # Remove "New Arrival" tags from outdated products
    remove_new_arrival_tag()
