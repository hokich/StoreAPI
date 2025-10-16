from search.services.search_query import (
    update_search_queries_popularity_indexes,
)
from store.services.attribute import (
    update_listings_attributes_popularity_indexes,
)
from store.services.catalog import update_catalogs_popularity_indexes
from store.services.product import (
    update_products_popularity_indexes,
    update_products_search_often_indexes,
)
from store.services.sections import update_bestsellers_products


def run() -> None:
    """Weekly scheduled task for recalculating popularity and sales indexes across products and categories."""
    # Update counters, calculate sales index, and assign "Bestseller" tag
    update_bestsellers_products()
    # Update counters and calculate popularity index for products
    update_products_popularity_indexes()
    # Update counters and calculate search frequency index for products
    update_products_search_often_indexes()
    # Update counters and calculate popularity index for catalogs
    update_catalogs_popularity_indexes()
    # Update counters and calculate popularity index for listing attributes
    update_listings_attributes_popularity_indexes()
    # Update counters and calculate popularity index for search queries
    update_search_queries_popularity_indexes()
