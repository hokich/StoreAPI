from typing import Optional

from django.db import models

from images.models import Image
from utils.exceptions import ObjectDoesNotExistException


class Banner(models.Model):
    """Represents a marketing banner with multiple display images."""

    name = models.CharField(max_length=255, verbose_name="Name")
    url = models.URLField(
        max_length=255, blank=True, null=True, verbose_name="Link"
    )
    created_at = models.DateField(auto_now_add=True, verbose_name="Created at")
    date_start = models.DateField(
        blank=True, null=True, verbose_name="Start date"
    )
    date_end = models.DateField(blank=True, null=True, verbose_name="End date")

    _tags = models.ManyToManyField(
        "store.Catalog", blank=True, related_name="_catalog_banners"
    )

    is_on_all_pages = models.BooleanField(
        default=False, verbose_name="Show on all pages"
    )
    is_active = models.BooleanField(default=True, verbose_name="Status")

    home_mobile_image = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Home image (Mobile)",
    )
    home_desktop_image = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Home image (Desktop)",
    )
    catalog_mobile_image = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Catalog image (Mobile)",
    )
    catalog_desktop_image = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Catalog image (Desktop)",
    )
    header_desktop_image = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Header image (Desktop)",
    )

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ["-created_at", "-pk"]

    @property
    def preview_image(self) -> Optional["Image"]:
        """Returns the first available image for preview (priority-based)."""
        if self.home_mobile_image:
            return self.home_mobile_image
        elif self.home_desktop_image:
            return self.home_desktop_image
        elif self.catalog_mobile_image:
            return self.catalog_mobile_image
        elif self.catalog_desktop_image:
            return self.catalog_desktop_image
        elif self.header_desktop_image:
            return self.header_desktop_image
        else:
            return None

    @classmethod
    def get_banner_by_pk(cls, pk: int) -> "Banner":
        """Returns banner by PK or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Banner with pk {pk} does not exist."}
            )
