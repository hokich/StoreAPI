from rest_framework import serializers

from customer.models import Customer
from reviews.models import Review
from reviews.services import CreateReviewTypedDict, create_review
from utils.validation import is_phone_valid


class PublishReviewSerializer(serializers.ModelSerializer):
    """Serializer for displaying published reviews."""

    class Meta:
        model = Review
        fields = [
            "id",
            "first_name",
            "rating",
            "comment",
            "advantages",
            "disadvantages",
            "created_at",
        ]


class ReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating new product reviews."""

    customer_id = serializers.CharField()
    first_name = serializers.CharField(max_length=100)
    rating = serializers.IntegerField()
    comment = serializers.CharField(max_length=500)
    phone = serializers.CharField(
        max_length=20, allow_null=True, allow_blank=True, required=False
    )
    advantages = serializers.CharField(
        max_length=500, allow_null=True, allow_blank=True, required=False
    )
    disadvantages = serializers.CharField(
        max_length=500, allow_null=True, allow_blank=True, required=False
    )

    def validate_customer_id(self, value: int) -> int:
        """Validates that a customer with the given session ID exists."""
        if not Customer.objects.filter(session_id=value).exists():
            raise serializers.ValidationError(
                f"Customer with session_id {value} does not exist."
            )
        return value

    def validate_phone(self, value: str) -> str:
        """Validates the phone number format."""
        if value and not is_phone_valid(value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value

    def validate_rating(self, value: int) -> int:
        """Validates that the rating value is between 1 and 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value

    def create(self, validated_data: dict) -> Review:
        """Creates a review using the `create_review` service function."""
        review_data: CreateReviewTypedDict = {
            "customer_id": validated_data["customer_id"],
            "first_name": validated_data["first_name"],
            "rating": validated_data["rating"],
            "comment": validated_data["comment"],
            "phone": validated_data.get("phone"),
            "advantages": validated_data.get("advantages"),
            "disadvantages": validated_data.get("disadvantages"),
            "reply_id": validated_data.get("reply_id", None),
        }
        return create_review(review_data)
