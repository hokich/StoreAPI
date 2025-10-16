from store.models import Product
from store.services.product import set_product_add_services


def run() -> None:
    """Sets additional services for all products."""
    products = Product.objects.all()
    i = 1
    count = products.count()
    for product in products:
        set_product_add_services(product.id)
        print(f"\rProcessing: {i}/{count}", end="", flush=True)
        i += 1
    print("\nProducts services have been set.")
