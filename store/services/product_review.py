from reviews.models import Review

from ..models import Product
from ..models.product_review import ProductReview


def create_product_review(product_id: int, review_id: int) -> "ProductReview":
    """Creates a product review entry linking a product and a review."""
    product = Product.get_product_by_pk(product_id)
    review = Review.get_review_by_pk(review_id)

    return ProductReview.objects.create(product=product, review=review)
