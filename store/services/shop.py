from store.models import Product, ProductInShop, Shop
from utils.exceptions import InvalidDataException


def create_product_in_shop(
    product_id: int, shop_id: int, quantity: int
) -> ProductInShop:
    """Creates a product entry in a shop."""
    product = Product.get_product_by_pk(product_id)
    shop = Shop.get_shop_by_pk(shop_id)

    if quantity < 0:
        raise InvalidDataException(
            {"message": "Quantity must be greater than or equal to 0."}
        )

    return ProductInShop.objects.create(
        product=product, shop=shop, quantity=quantity
    )
