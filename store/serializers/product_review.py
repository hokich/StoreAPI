from rest_framework import serializers

from reviews.models import Review
from reviews.serializers import PublishReviewSerializer, ReviewCreateSerializer

from ..models import Product, ProductReview
from ..services.product_review import create_product_review


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for the ProductReview model, returning the linked review."""

    class Meta:
        model = ProductReview

    def to_representation(self, instance: ProductReview) -> dict:
        """Return the serialized data of the related review."""
        serializer = PublishReviewSerializer(instance.review)
        return serializer.data


class ProductReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating a review linked to a specific product."""

    product_id = serializers.IntegerField()
    review = ReviewCreateSerializer()

    def validate_product_id(self, value: int) -> int:
        """Validate that the product with the given ID exists."""
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"Product with id {value} does not exist."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """Perform nested validation for the review data."""
        review_serializer = ReviewCreateSerializer(data=attrs["review"])
        review_serializer.is_valid(raise_exception=True)
        return attrs

    def create(self, validated_data: dict) -> Review:
        """Create a review and link it to the specified product."""
        product_id = validated_data["product_id"]
        review_data = validated_data["review"]

        review_instance = ReviewCreateSerializer().create(review_data)
        create_product_review(product_id, review_instance.pk)

        return review_instance
