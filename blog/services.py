from typing import Optional, TypedDict

from django.core.files import File
from django.core.files.uploadedfile import UploadedFile

from blog.models import Article
from images.services import create_image
from utils.translit import to_chpu


def _get_slug_by_name(name: str) -> str:
    """Generates a unique slug (SEO URL) based on the article name."""
    slug = to_chpu(name)
    while _check_article_exists_by_slug(slug):
        slug = to_chpu(name, last_slug=slug)
    return slug


def _check_article_exists_by_slug(slug: str) -> bool:
    """Checks if an article with the given slug already exists."""
    return Article.objects.filter(slug=slug).exists()


def create_article(name: str, is_publish: bool = False) -> Article:
    """Creates a new article with a generated slug."""
    slug = _get_slug_by_name(name)
    return Article.objects.create(name=name, slug=slug, is_publish=is_publish)


def set_products_in_article(article_id: int, products_ids: list[int]) -> None:
    """Links selected products to the article."""
    article = Article.get_article_by_pk(article_id)
    article._products._tags.set(products_ids)


def set_article_image(
    article_id: int, image_file: Optional[UploadedFile | File] = None
) -> Article:
    """Sets or removes the main image for the article."""
    article = Article.get_article_by_pk(article_id)

    if image_file is None:
        if article.image:
            article.image.delete()
        article.image = None
        article.save()
        return article

    if article.image:
        article.image.delete()

    article_image = create_image(
        name=f"{article.slug}_image",
        object_type="article",
        image_file=image_file,
        max_width=1920,
        max_height=1080,
        alt_text=article.name,
    )

    article.image = article_image
    article.save()
    return article


class UpdateArticleDict(TypedDict, total=True):
    """Typed dictionary for updating article fields."""

    name: str
    is_publish: bool


def update_article(
    article_id: int,
    article_data: UpdateArticleDict,
) -> Article:
    """Updates article name, slug, and publish status."""
    article = Article.get_article_by_pk(article_id)

    slug = article.slug
    if article.name != article_data["name"]:
        slug = _get_slug_by_name(article_data["name"])

    article.name = article_data["name"]
    article.slug = slug
    article.is_publish = article_data["is_publish"]

    article.save()
    return article
