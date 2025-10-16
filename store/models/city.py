from django.db import models

from utils.exceptions import ObjectDoesNotExistException


class City(models.Model):
    """Represents a city."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Name")
    order = models.SmallIntegerField(
        blank=True, null=True, verbose_name="Sort order position"
    )

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_city_by_pk(cls, city_id: int) -> "City":
        """Returns a city by its primary key."""
        try:
            return cls.objects.get(pk=city_id)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"City with pk '{city_id}' does not exist."}
            )
