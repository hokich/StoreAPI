from typing import Any

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from utils.exceptions import PageNotFoundException
from utils.response_service import ResponseService

from .models import Article
from .serializers import ArticleBriefSerializer, ArticleSerializer


ARTICLES_PAGE_SIZE = 10


class ArticlesPagination(PageNumberPagination):
    """Fixed-size page number pagination for articles."""

    page_size = ARTICLES_PAGE_SIZE
    max_page_size = ARTICLES_PAGE_SIZE

    def paginate_queryset(self, *args: Any, **kwargs: Any) -> Any:
        """Paginates a queryset; maps DRF NotFound to a domain-specific exception."""
        try:
            return super().paginate_queryset(*args, **kwargs)
        except NotFound:
            raise PageNotFoundException({"message": "Page does not exist."})


class ArticleViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    """ViewSet for published articles: list, retrieve, and sitemap data."""

    queryset = (
        Article.objects.filter(is_publish=True)
        .select_related("image", "_article_page")
        .prefetch_related("_products")
        .order_by("-created_at")
    )
    lookup_field = "slug"

    def get_serializer_class(self) -> Any:
        """Chooses brief serializer for list, full serializer for retrieve."""
        if self.action == "list":
            return ArticleBriefSerializer
        elif self.action == "retrieve":
            return ArticleSerializer

    def retrieve(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Returns a single article by slug."""
        instance = Article.get_article_by_slug(kwargs["slug"])
        serializer = self.get_serializer(instance)
        return ResponseService.success(serializer.data)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Returns a paginated list of published articles."""
        queryset = self.get_queryset()

        paginator = ArticlesPagination()
        paginated_articles = paginator.paginate_queryset(queryset, request)

        serializer = self.get_serializer(paginated_articles, many=True)
        return ResponseService.success(
            {"items": serializer.data, "count": queryset.count()}
        )

    @action(detail=False, methods=["get"], url_path="sitemap-data")
    def sitemap_data(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Returns a flat list of article slugs for sitemap generation."""
        articles_slugs = Article.objects.filter(is_publish=True).values_list(
            "slug", flat=True
        )

        return ResponseService.success(list(articles_slugs))
