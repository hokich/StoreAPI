from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from store.serializers.product_review import ProductReviewCreateSerializer
from utils.response_service import ResponseService


class CreateProductReviewView(APIView):
    def post(self, request: Request) -> Response:
        """
        Handles POST request to create a product review.
        """
        serializer = ProductReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return ResponseService.success({})
