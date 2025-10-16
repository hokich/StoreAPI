from typing import Optional

from django.db import models

from utils.exceptions import ObjectDoesNotExistException


class ShortLink(models.Model):
    """Represents a shortened URL with a unique slug."""

    slug = models.SlugField("Slug", max_length=255, unique=True)
    link = models.CharField(max_length=255, verbose_name="Link")

    class Meta:
        verbose_name = "Short link"
        verbose_name_plural = "Short links"
        ordering = ["-pk"]

    @classmethod
    def get_link_by_pk(cls, pk: int) -> "ShortLink":
        """Returns a short link by its primary key or raises an exception if not found."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"ShortLink with pk '{pk}' does not exist."}
            )

    @classmethod
    def find_link_by_pk(cls, pk: int) -> Optional["ShortLink"]:
        """Finds a short link by primary key or returns None if it doesn’t exist."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_link_by_slug(cls, slug: str) -> "ShortLink":
        """Returns a short link by its slug or raises an exception if not found."""
        try:
            return cls.objects.get(slug=slug)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"ShortLink with slug '{slug}' does not exist."}
            )
