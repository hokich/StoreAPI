from django.db.models import Prefetch, QuerySet

from customer.models import Customer
from store.models import Product
from store.services.attribute import (
    get_products_attributes_queryset_for_prefetch,
)

from .models import CompareProduct


def add_product_to_compare(
    customer_id: int, product_id: int
) -> CompareProduct:
    """
    Adds a product to the customer's compare list.

    :param customer_id: Customer ID
    :param product_id: Product ID to be added to comparison
    :return: Created CompareProduct instance
    """

    customer = Customer.get_customer_by_pk(customer_id)
    product = Product.get_product_by_pk(product_id, publish=True)

    compare_product = CompareProduct.objects.create(
        customer=customer,
        product=product,
    )

    return compare_product


def delete_product_from_compare(customer_id: int, product_id: int) -> None:
    """
    Removes a product from the compare list.

    :param customer_id: Customer ID
    :param product_id: Product ID to be removed from comparison
    """

    try:
        compare_product = CompareProduct.objects.get(
            customer_id=customer_id, product_id=product_id
        )
        compare_product.delete()
    except CompareProduct.DoesNotExist:
        pass


def clear_compare(customer_id: int) -> None:
    """
    Clears all products from the customer's compare list.

    :param customer_id: Customer ID whose compare list will be cleared
    """

    compare_products = CompareProduct.objects.filter(customer_id=customer_id)
    compare_products.delete()


def get_compare_products(customer_id: int) -> "QuerySet[CompareProduct]":
    """
    Returns a queryset of products in the customer's compare list.
    Includes only published products, ordered by date added,
    and prefetches related data for performance optimization.
    """

    return (
        CompareProduct.objects.filter(
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
        .order_by("date_added")
    )


def get_brief_compare_product(
    customer_id: int,
) -> "QuerySet[CompareProduct]":
    """
    Returns a brief queryset of products in the customer's compare list.
    Includes only published products, ordered by date added,
    with basic related image data prefetched.
    """

    return (
        CompareProduct.objects.filter(
            customer_id=customer_id, product__publish=True
        )
        .select_related("product")
        .prefetch_related(
            "product___images",
            "product___images__thumb_image",
            "product___images__sd_image",
            "product___images__hd_image",
        )
        .order_by("date_added")
    )
