from typing import Any, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import QuerySet

from customer.models import Customer
from store.models import Product
from utils.exceptions import ObjectDoesNotExistException
from web_pages.models import ArticlePage


class Article(models.Model):
    """Represents a blog or informational article with related products and reviews."""

    name = models.CharField(max_length=255, verbose_name="Title")
    slug = models.SlugField("Slug", max_length=255, unique=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created at"
    )
    image = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Image",
    )
    is_publish = models.BooleanField(default=1, verbose_name="Published?")
    likes = models.IntegerField(default=0, verbose_name="Likes count")
    dislikes = models.IntegerField(default=0, verbose_name="Dislikes count")
    views_count = models.IntegerField(default=0, verbose_name="Views count")

    _products = models.ManyToManyField(
        "store.Product",
        blank=True,
        related_name="articles",
        verbose_name="Products in article",
    )
    _reviews = models.ManyToManyField(
        "reviews.Review",
        blank=True,
        related_name="+",
        verbose_name="Reviews",
    )

    _page = None

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self) -> str:
        return self.name

    @property
    def article_products(self) -> "QuerySet[Product]":
        """Returns only published products linked to this article."""
        return self._products.filter(publish=True)

    @property
    def page(self) -> Optional["ArticlePage"]:
        """Returns or initializes a related ArticlePage object."""
        if not self._page:
            try:
                self._page = self._article_page
            except ObjectDoesNotExist:
                self._page = ArticlePage(article=self)
        return self._page

    def like(self, customer: Customer) -> None:
        """Adds or toggles a 'like' reaction for this article."""
        existing_reaction = ArticleCustomerReaction.objects.filter(
            article=self, customer=customer
        ).first()

        if existing_reaction:
            if existing_reaction.is_like:
                existing_reaction.delete()
                self.likes -= 1
            else:
                existing_reaction.is_like = True
                existing_reaction.save()
                self.likes += 1
                self.dislikes -= 1
        else:
            ArticleCustomerReaction.objects.create(
                article=self, customer=customer, is_like=True
            )
            self.likes += 1

        self.save()

    def dislike(self, customer: Customer) -> None:
        """Adds or toggles a 'dislike' reaction for this article."""
        existing_reaction = ArticleCustomerReaction.objects.filter(
            article=self, customer=customer
        ).first()

        if existing_reaction:
            if not existing_reaction.is_like:
                existing_reaction.delete()
                self.dislikes -= 1
            else:
                existing_reaction.is_like = False
                existing_reaction.save()
                self.likes -= 1
                self.dislikes += 1
        else:
            ArticleCustomerReaction.objects.create(
                article=self, customer=customer, is_like=False
            )
            self.dislikes += 1

        self.save()

    @classmethod
    def get_article_by_pk(cls, pk: int, **kwargs: Any) -> "Article":
        """Returns an article by PK or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(pk=pk, **kwargs)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Article with pk '{pk}' does not exist."}
            )

    @classmethod
    def find_article_by_pk(cls, pk: int, **kwargs: Any) -> Optional["Article"]:
        """Finds an article by PK or returns None."""
        try:
            return cls.objects.get(pk=pk, **kwargs)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_article_by_slug(cls, slug: str, **kwargs: Any) -> "Article":
        """Returns an article by slug or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(slug=slug, **kwargs)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Article with slug '{slug}' does not exist."}
            )


class ArticleCustomerReaction(models.Model):
    """Stores user reaction (like/dislike) for an article."""

    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        verbose_name="Customer",
    )
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, verbose_name="Article"
    )
    is_like = models.BooleanField(default=True, verbose_name="Is like?")

    class Meta:
        unique_together = ("customer", "article")
