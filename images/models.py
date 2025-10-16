import os
from typing import Any

from django.db import models


class Image(models.Model):
    image = models.ImageField(verbose_name="Image")
    alt = models.CharField(
        max_length=255, verbose_name="Alt text", blank=True, null=True
    )

    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"
        ordering = ["id"]

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """
        Override of the delete method to remove the image file from storage.
        """
        # First, try to delete the physical image file if it exists
        if self.image and hasattr(self.image, "path"):
            try:
                if os.path.isfile(self.image.path):
                    os.remove(self.image.path)
            except Exception as e:
                # Handle possible file deletion errors
                print(f"Error deleting file {self.image.path}: {e}")

        # Then call the default delete method to remove the DB entry
        super().delete(*args, **kwargs)
