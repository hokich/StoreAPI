from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from customer.models import Customer
from store.models import Product
from store.services.attribute import (
    get_products_attributes_queryset_for_prefetch,
)

from .models import FavoriteProduct


def add_product_to_favorites(
    customer_id: int, product_id: int
) -> FavoriteProduct:
    """
    Adds a product to the customer's favorites list.

    :param customer_id: Customer ID
    :param product_id: Product ID to be added to favorites
    :return: The created or updated FavoriteProduct instance
    """
    customer = Customer.get_customer_by_pk(customer_id)
    product = Product.get_product_by_pk(product_id)

    favorite_product, _ = FavoriteProduct.objects.update_or_create(
        customer=customer,
        product=product,
        defaults={"date_added": timezone.now()},
    )

    return favorite_product


def delete_product_from_favorites(customer_id: int, product_id: int) -> None:
    """
    Removes a product from the customer's favorites list.

    :param customer_id: Customer ID
    :param product_id: Product ID to be removed from favorites
    """
    try:
        favorite_product = FavoriteProduct.objects.get(
            customer_id=customer_id, product_id=product_id
        )
        favorite_product.delete()
    except FavoriteProduct.DoesNotExist:
        pass


def clear_favorites(customer_id: int) -> None:
    """
    Clears all favorite products for the given customer.

    :param customer_id: Customer ID whose favorites should be cleared
    """
    favorite_products = FavoriteProduct.objects.filter(customer_id=customer_id)
    favorite_products.delete()


def get_favorites_product(customer_id: int) -> "QuerySet[FavoriteProduct]":
    """
    Retrieves a queryset of the customer’s favorite products.
    Only published products (publish=True) are returned, ordered by date added,
    with related data preloaded for query optimization.
    """
    return (
        FavoriteProduct.objects.filter(
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
        .order_by("-date_added")
    )


def get_brief_favorites_product(
    customer_id: int,
) -> "QuerySet[FavoriteProduct]":
    """
    Retrieves a brief queryset of the customer’s favorite products.
    Only published products (publish=True) are returned, ordered by date added,
    with lightweight prefetching for optimization.
    """
    return (
        FavoriteProduct.objects.filter(
            customer_id=customer_id, product__publish=True
        )
        .select_related("product")
        .prefetch_related(
            "product___images",
            "product___images__thumb_image",
            "product___images__sd_image",
            "product___images__hd_image",
        )
        .order_by("-date_added")
    )
