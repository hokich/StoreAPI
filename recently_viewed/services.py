from datetime import timedelta

from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from customer.models import Customer
from store.models import Product
from store.services.attribute import (
    get_products_attributes_queryset_for_prefetch,
)

from .models import RecentlyViewed


def create_or_update_recently_viewed(
    customer_id: int, product_id: int
) -> "RecentlyViewed":
    """
    Creates or updates a record of a recently viewed product.

    :param customer_id: ID of the customer.
    :param product_id: ID of the viewed product.
    :return: The created or updated RecentlyViewed instance.
    """
    customer = Customer.get_customer_by_pk(customer_id)
    product = Product.get_product_by_pk(product_id)

    recently_viewed, _ = RecentlyViewed.objects.update_or_create(
        customer=customer,
        product=product,
        defaults={"date_viewed": timezone.now()},
    )
    return recently_viewed


def delete_old_viewed_products(age_in_seconds: int) -> int:
    """
    Deletes recently viewed products older than the given age.

    :param age_in_seconds: Number of seconds after which viewed products are considered outdated.
    :return: Number of deleted records.
    """
    threshold_time = timezone.now() - timedelta(seconds=age_in_seconds)

    old_viewed_products = RecentlyViewed.objects.filter(
        date_viewed__lt=threshold_time
    )

    deleted_count, _ = old_viewed_products.delete()

    return deleted_count


def get_recently_viewed(customer_id: int) -> "QuerySet[RecentlyViewed]":
    """
    Returns a queryset of recently viewed products for the given customer.
    Only includes published products (publish=True), ordered by view date (descending),
    with prefetching for related data to optimize queries.

    :param customer_id: ID of the customer.
    :return: QuerySet of RecentlyViewed instances.
    """
    return (
        RecentlyViewed.objects.filter(
            customer_id=customer_id, product__publish=True
        )
        .select_related("product")
        .prefetch_related(
            "product___images",
            "product___images__thumb_image",
            "product___images__sd_image",
            "product___images__hd_image",
            "product___tags",
            Prefetch(
                "product___product_attributes",
                queryset=get_products_attributes_queryset_for_prefetch(),
            ),
        )
        .order_by("-date_viewed")
    )
