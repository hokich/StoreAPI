from typing import Optional

from store.models import Product, ProductAddService
from utils.exceptions import InvalidDataException, ObjectDoesNotExistException

from .models import Cart, CartProduct, CartProductAddService


def create_cart() -> Cart:
    """Creates a new empty cart."""
    return Cart.objects.create()


def add_product_to_cart(
    cart_id: int, product_id: int, quantity: int = 1
) -> CartProduct:
    """
    Adds a product to the cart or updates its quantity.

    :param cart_id: Cart ID
    :param product_id: Product ID to add
    :param quantity: Product quantity (default 1)
    :return: CartProduct instance
    """
    if quantity < 1:
        raise InvalidDataException(
            {"message": "Quantity must be greater than 0"}
        )

    cart = Cart.get_cart_by_pk(cart_id)
    product = Product.get_product_by_pk(product_id)

    try:
        cart_product = CartProduct.objects.get(cart=cart, product=product)
        cart_product.quantity = quantity
        cart_product.save()
    except CartProduct.DoesNotExist:
        cart_product = CartProduct.objects.create(
            cart=cart, product=product, quantity=quantity
        )

    return cart_product


def delete_product_from_cart(cart_id: int, product_id: int) -> Optional[dict]:
    """
    Removes a product from the cart.

    :param cart_id: Cart ID
    :param product_id: Product ID to remove
    :return: Deleted product data or None if not found
    """
    from .serializers import AddedCartProductSerializer

    cart = Cart.get_cart_by_pk(cart_id)

    try:
        cart_product = CartProduct.objects.get(
            cart=cart, product_id=product_id
        )
        deleted_cart_product_data = AddedCartProductSerializer(
            cart_product
        ).data
        cart_product.delete()
        return deleted_cart_product_data
    except CartProduct.DoesNotExist:
        return None


def add_service_for_product(
    cart_id: int, product_id: int, service_id: int
) -> "CartProductAddService":
    """
    Adds a service to a product in the cart.

    :param cart_id: Cart ID
    :param product_id: Product ID
    :param service_id: Service ID
    :return: CartProductAddService instance
    """
    cart = Cart.get_cart_by_pk(cart_id)

    try:
        cart_product = CartProduct.objects.get(
            cart=cart, product_id=product_id
        )
    except CartProduct.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Product with ID {product_id} not found in cart {cart_id}"
            }
        )

    try:
        service = ProductAddService.get_service_by_pk(
            service_id, product=cart_product.product
        )
    except ObjectDoesNotExistException:
        raise ObjectDoesNotExistException(
            {
                "message": f"Service with pk '{service_id}' does not exist for product with pk {cart_product.product.id}."
            }
        )

    try:
        cart_product_add_service = CartProductAddService.objects.get(
            cart_product=cart_product, service=service
        )
        cart_product_add_service.active = True
        cart_product_add_service.save()
    except CartProductAddService.DoesNotExist:
        cart_product_add_service = CartProductAddService.objects.create(
            cart_product=cart_product, service=service, active=True
        )

    return cart_product_add_service


def set_cart_product_services(
    cart_id: int, product_id: int, services_ids: list[int]
) -> "CartProduct":
    """
    Sets multiple services for a specific cart product.

    :return: CartProduct instance
    """
    cart = Cart.get_cart_by_pk(cart_id)
    try:
        cart_product = CartProduct.objects.get(
            cart=cart, product_id=product_id
        )
    except CartProduct.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Product with ID {product_id} not found in cart {cart_id}"
            }
        )

    cart_product._services.set(services_ids)

    return cart_product


def change_service_status_for_product(
    cart_id: int, product_id: int, service_id: int, active: bool
) -> "CartProductAddService":
    """
    Updates the active status of a service for a product in the cart.

    :param cart_id: Cart ID
    :param product_id: Product ID
    :param service_id: Service ID
    :param active: New active status
    :return: Updated CartProductAddService instance
    """
    cart = Cart.get_cart_by_pk(cart_id)

    try:
        cart_product = CartProduct.objects.get(
            cart=cart, product_id=product_id
        )
    except CartProduct.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Product with ID {product_id} not found in cart {cart_id}"
            }
        )

    service = ProductAddService.get_service_by_pk(service_id)

    try:
        cart_product_add_service = CartProductAddService.objects.get(
            cart_product=cart_product, service=service
        )
        cart_product_add_service.active = active
        cart_product_add_service.save()
    except CartProductAddService.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Service with ID {service_id} not found for product {product_id} in cart {cart_id}"
            }
        )

    return cart_product_add_service


def delete_service_for_product(
    cart_id: int, product_id: int, service_id: int
) -> None:
    """
    Deletes a service linked to a specific product in the cart.

    :param cart_id: Cart ID
    :param product_id: Product ID
    :param service_id: Service ID
    """
    cart = Cart.get_cart_by_pk(cart_id)

    try:
        cart_product = CartProduct.objects.get(
            cart=cart, product_id=product_id
        )
    except CartProduct.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Product with ID {product_id} not found in cart {cart_id}"
            }
        )

    try:
        cart_product_add_service = CartProductAddService.objects.get(
            cart_product=cart_product, service_id=service_id
        )
        cart_product_add_service.delete()
    except CartProductAddService.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Service with ID {service_id} not found for product {product_id} in cart {cart_id}"
            }
        )


def clear_cart(cart_id: int) -> None:
    """
    Clears the cart, removing all products and linked services.

    :param cart_id: Cart ID
    """
    cart = Cart.get_cart_by_pk(cart_id)
    CartProduct.objects.filter(cart=cart).delete()
