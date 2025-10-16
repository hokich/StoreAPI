from typing import Optional, TypedDict

from customer.models import Customer

from .models import Review


class CreateReviewTypedDict(TypedDict, total=True):
    """TypedDict for structured review creation data."""

    customer_id: str
    first_name: str
    rating: int
    comment: str
    phone: Optional[str]
    advantages: Optional[str]
    disadvantages: Optional[str]
    reply_id: Optional[int]


def create_review(review_data: CreateReviewTypedDict) -> Review:
    """Creates a new review based on the provided data."""
    customer = Customer.get_customer_by_session_id(review_data["customer_id"])

    reply_obj: Optional[Review] = None
    if review_data["reply_id"]:
        reply_obj = Review.get_review_by_pk(review_data["reply_id"])

    return Review.objects.create(
        customer=customer,
        first_name=review_data["first_name"],
        rating=review_data["rating"],
        comment=review_data["comment"],
        phone=review_data["phone"],
        advantages=review_data["advantages"],
        disadvantages=review_data["disadvantages"],
        reply=reply_obj,
    )


def set_is_publish_review(review_id: int, is_publish: bool) -> Review:
    """Updates the publication status of a review."""
    review = Review.get_review_by_pk(review_id)
    review.is_publish = is_publish
    review.save()
    return review
