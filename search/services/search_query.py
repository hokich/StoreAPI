from typing import Optional, TypedDict

from django.db.models import QuerySet

from store.models import Catalog
from store.services.catalog import get_catalog_tree

from ..models import SearchQuery
from ..serializers import SearchQuerySerializer
from .client import MeiliSearchClient


def create_search_query(
    text: str,
    catalog_id: Optional[int] = None,
    is_publish: bool = True,
    is_moderation: bool = False,
) -> SearchQuery:
    """
    Creates a search query.

    :param text: Query text.
    :param catalog_id: Catalog ID to associate (optional).
    :param is_publish: Whether the query is published.
    :param is_moderation: Whether the query is approved (moderated).
    :return: Created SearchQuery instance.
    """
    catalog = None
    if catalog:
        catalog = Catalog.get_object_by_pk(catalog_id)

    search_query = SearchQuery.objects.create(
        text=text,
        catalog=catalog,
        is_publish=is_publish,
        is_moderation=is_moderation,
    )
    return search_query


def create_or_increment_search_query(text: str) -> SearchQuery:
    """
    Creates a new search query or increments the request counter for an existing one.

    :param text: Query text.
    :return: SearchQuery instance.
    """
    text = text.lower().strip()
    search_query = SearchQuery.find_query_by_text(text)
    if search_query:
        search_query.increment_count_requests()
    else:
        search_query = create_search_query(text)

    search_query.popular.index_counter_increment()

    return search_query


def update_search_query(
    search_query_id: int,
    text: str,
    catalog_id: Optional[int] = None,
) -> SearchQuery:
    """
    Updates a search query.

    :param search_query_id: SearchQuery ID.
    :param text: New query text.
    :param catalog_id: Catalog ID to associate (optional).
    :return: Updated SearchQuery instance.
    """
    search_query = SearchQuery.get_query_by_pk(search_query_id)
    catalog = None
    if catalog_id:
        catalog = Catalog.get_object_by_pk(catalog_id)

    search_query.text = text
    search_query.catalog = catalog
    search_query.save()

    return search_query


def update_publish_search_query(
    search_query_id: int, is_publish: bool
) -> SearchQuery:
    """
    Updates the publication status of a search query.

    :param search_query_id: SearchQuery ID.
    :param is_publish: Publication flag.
    :return: Updated SearchQuery instance.
    """
    search_query = SearchQuery.get_query_by_pk(search_query_id)
    search_query.is_publish = is_publish
    search_query.save()

    return search_query


def update_moderation_search_query(
    search_query_id: int, is_moderation: bool
) -> SearchQuery:
    """
    Updates the moderation (approval) status of a search query.

    :param search_query_id: SearchQuery ID.
    :param is_moderation: Moderation flag.
    :return: Updated SearchQuery instance.
    """
    search_query = SearchQuery.get_query_by_pk(search_query_id)
    search_query.is_moderation = is_moderation
    search_query.save()

    return search_query


def delete_search_query(search_query_id: int) -> None:
    """
    Deletes a search query.

    :param search_query_id: SearchQuery ID.
    """
    search_query = SearchQuery.get_query_by_pk(search_query_id)
    search_query.delete()


def get_search_queries(
    text_query: Optional[str] = None,
    is_publish: Optional[bool] = True,
    is_moderation: Optional[bool] = None,
) -> "QuerySet[SearchQuery]":
    """
    Retrieves search queries with optional filters.

    :param text_query: Text to search within query text (icontains).
    :param is_publish: Filter by publication status (None to skip).
    :param is_moderation: Filter by moderation status (None to skip).
    :return: QuerySet of SearchQuery.
    """
    search_queries = SearchQuery.objects.all()
    if text_query is not None:
        search_queries = search_queries.filter(text__icontains=text_query)
    if is_publish is not None:
        search_queries = search_queries.filter(is_publish=is_publish)
    if is_moderation is not None:
        search_queries = search_queries.filter(is_moderation=is_moderation)
    return search_queries


def search_products_and_catalogs(
    query: str, limit_products: int = 20, limit_catalogs: int = 4
) -> tuple[list[dict], list[dict]]:
    """Searches products and catalogs in MeiliSearch and returns their hits."""
    ms_client = MeiliSearchClient()

    ms_products = ms_client.search_products(
        query,
        in_stock_only=True,
        attributes_to_retrieve=[
            "id",
            "sku",
            "name",
            "slug",
            "url",
            "price",
            "discountedPrice",
            "bonusesAmount",
            "rating",
            "reviewsCount",
            "images",
            "status",
        ],
        limit=limit_products,
    )["hits"]
    ms_catalogs = ms_client.search_catalog(query, limit=limit_catalogs)["hits"]

    return ms_products, ms_catalogs


def find_top_parent_category(
    categories: list, target_slug: str, top_parent: Optional[str] = None
) -> Optional[str]:
    """
    Recursively finds a category by `target_slug` and returns the name of the top-level parent category.

    :param categories: Category tree to search.
    :param target_slug: Target listing slug.
    :param top_parent: Current top-level parent name in traversal.
    :return: Top-level parent category name, or None if not found.
    """
    for category in categories:
        if "children" in category:
            # If we're at the top level (top_parent not set), set current as top parent
            current_top_parent = (
                top_parent if top_parent is not None else category["name"]
            )
            for child in category["children"]:
                if child["slug"] == target_slug:
                    # Return top parent when the target is found
                    return current_top_parent
                else:
                    # Continue searching in child nodes, preserving current_top_parent
                    result = find_top_parent_category(
                        [child], target_slug, current_top_parent
                    )
                    if result is not None:
                        return result
    return None  # Not found


def search_for_page(query: str) -> tuple:
    """Aggregates search results for the search page: listings with products, categories with listings, and total hits."""
    ms_client = MeiliSearchClient()

    search_result = ms_client.search_products(
        query,
        facets_list=["listingSlug"],
        in_stock_only=True,
        limit=10000,
    )

    ms_products = search_result["hits"]

    listing_facets = search_result["facetDistribution"]["listingSlug"]

    categories_with_listings: dict = {}
    listings_with_products = []
    catalogs_tree = get_catalog_tree()
    for listing_slug, count in listing_facets.items():
        if not count:
            continue

        products_list = []
        for product in ms_products:
            if product["listing"]["slug"] != listing_slug:
                continue
            products_list.append(product)
            if len(products_list) >= 10:
                break

        listing = products_list[0]["listing"]
        listings_with_products.append(
            {
                "listing": listing,
                "products": products_list,
                "products_count": count,
            }
        )

        parent_category_name = find_top_parent_category(
            catalogs_tree, listing_slug
        )
        listing_json = {"listing": listing, "products_count": count}

        if parent_category_name in categories_with_listings:
            categories_with_listings[parent_category_name].append(listing_json)
        else:
            categories_with_listings[parent_category_name] = [listing_json]

    return (
        listings_with_products,
        categories_with_listings,
        search_result["estimatedTotalHits"],
    )


class SearchHints(TypedDict):
    """Structured hints response with popular queries and next-word suggestions."""

    queries: list[dict]
    words: list[str]


def get_hints_by_query(query: str) -> SearchHints:
    """Returns popular search queries and next-word suggestions for the given query."""
    queries = get_search_queries(
        query.strip(), is_publish=True, is_moderation=True
    ).order_by("-popular___index")[:4]

    ms_client = MeiliSearchClient()
    words = ms_client.get_suggestions(query, count=4)
    return {
        "queries": SearchQuerySerializer(queries, many=True).data,
        "words": words,
    }


def update_search_queries_popularity_indexes() -> None:
    """Recalculates popularity indexes for all search queries."""
    search_queries = SearchQuery.objects.all()
    for search_query in search_queries:
        search_query.popular.update_index()
