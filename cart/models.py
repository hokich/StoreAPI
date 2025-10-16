from decimal import Decimal

from django.db import models
from django.db.models import F, QuerySet, Sum

from utils.exceptions import ObjectDoesNotExistException


class Cart(models.Model):
    """Shopping cart with products and optional add-on services."""

    _products = models.ManyToManyField(
        "store.Product", through="CartProduct", verbose_name="Products in cart"
    )

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    @property
    def products(self) -> "QuerySet[CartProduct]":
        """Returns cart items with published products in stock."""
        return self._cart_products.filter(
            product__publish=True,
            product__quantity__gt=0,
        )

    @property
    def total_quantity(self) -> int:
        """Returns total quantity of all items in the cart."""
        value = self.products.aggregate(total_quantity=models.Sum("quantity"))[
            "total_quantity"
        ]
        return value if value else 0

    @property
    def total_services_price(self) -> int:
        """Returns total price of all active add-on services in the cart."""
        total_services_price = CartProductAddService.objects.filter(
            cart_product__cart=self,
            cart_product__product__publish=True,
            cart_product__product__quantity__gt=0,
            active=True,
        ).aggregate(
            total_price=Sum(F("service__price") * F("cart_product__quantity"))
        )[
            "total_price"
        ]

        return total_services_price or 0

    @property
    def total_price(self) -> int:
        """Returns total price of products plus add-on services (rounded)."""
        value = self.products.annotate(
            products_price=F("product__price") * F("quantity"),
        ).aggregate(total_price=Sum("products_price"))["total_price"]
        return round(value + self.total_services_price) if value else 0

    @property
    def total_discount_amount(self) -> int:
        """Returns total discount amount across all discounted products."""
        value = (
            self.products.exclude(product__discount_percent=0)
            .annotate(
                products_discount_amount=models.F("product__price")
                * models.F("product__discount_percent")
                / 100
                * models.F("quantity")
            )
            .aggregate(
                total_discount_amount=models.Sum("products_discount_amount")
            )["total_discount_amount"]
        )
        return round(value) if value else 0

    @property
    def total_discount_price(self) -> int:
        """Returns total price after product discounts plus add-on services."""
        value = (
            self.products.annotate(
                products_price=models.F("product__price")
                * models.F("quantity"),
                products_discount_amount=models.F("product__price")
                * models.F("product__discount_percent")
                / 100
                * models.F("quantity"),
            )
            .annotate(
                discounted_price=models.F("products_price")
                - models.F("products_discount_amount")
            )
            .aggregate(total_discounted_price=models.Sum("discounted_price"))[
                "total_discounted_price"
            ]
        )

        return round(value + self.total_services_price) if value else 0

    @property
    def total_bonuses_amount_dict(self) -> dict[str, int] | None:
        """Aggregates bonus amounts per level ('1','2','3') across items."""
        bonuses_list = [
            p.product.bonuses_amount_dict
            for p in self.products
            if p.product.bonuses_amount_dict is not None
        ]

        if not bonuses_list:
            return None

        return {
            key: sum(d.get(key, 0) for d in bonuses_list)
            for key in ("1", "2", "3")
        }

    def clean_cart(self) -> None:
        """Removes all items from the cart."""
        self._cart_products.all().delete()

    def get_cart_with_bonuses_and_rewards(
        self, *, total_bonuses_to_spend: int, account_level: str
    ) -> dict:
        """Returns detailed pricing with applied/earned bonuses per item."""
        results = []
        total_applied_bonuses = 0
        total_earned_bonuses = 0
        final_total_price = Decimal("0.00")
        remaining_bonuses = total_bonuses_to_spend

        all_cart_items = list(
            self._cart_products.select_related("product").all()
        )

        for cart_item in all_cart_items:
            product = cart_item.product
            quantity = cart_item.quantity

            for _ in range(quantity):
                if remaining_bonuses <= 0 or not product.can_accrue_bonuses:
                    applied_bonuses = 0
                else:
                    max_bonuses = product.get_max_spendable_bonuses()
                    applied_bonuses = min(max_bonuses, remaining_bonuses)
                    remaining_bonuses -= applied_bonuses
                    total_applied_bonuses += applied_bonuses

                discounted_price = product.discounted_price
                final_price = discounted_price - applied_bonuses
                earned_bonuses = product.calculate_earned_bonuses(
                    applied_bonuses=applied_bonuses,
                    account_level=account_level,
                )

                total_earned_bonuses += earned_bonuses
                final_total_price += final_price

                results.append(
                    {
                        "product_sku": product.sku,
                        "product_name": product.name,
                        "original_price": product.price,
                        "discounted_price": discounted_price,
                        "quantity": 1,
                        "applied_bonuses": applied_bonuses,
                        "final_price": final_price,
                        "earned_bonuses": earned_bonuses,
                    }
                )

        return {
            "items": results,
            "total_applied_bonuses": total_applied_bonuses,
            "total_earned_bonuses": total_earned_bonuses,
            "final_total_price": final_total_price,
        }

    @classmethod
    def get_cart_by_pk(cls, pk: int) -> "Cart":
        """Returns cart by PK or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Cart with pk '{pk}' does not exist."}
            )


class CartProduct(models.Model):
    """Cart line item for a specific product and quantity."""

    cart = models.ForeignKey(
        "Cart",
        on_delete=models.CASCADE,
        related_name="_cart_products",
        verbose_name="Cart",
    )
    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Product",
    )

    _services = models.ManyToManyField(
        "store.ProductAddService",
        through="CartProductAddService",
        verbose_name="Add-on services",
    )

    quantity = models.IntegerField(default=1, verbose_name="Quantity")
    date_added = models.DateTimeField(
        auto_now_add=True, verbose_name="Date added"
    )

    class Meta:
        verbose_name = "Cart item"
        verbose_name_plural = "Cart items"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "cart"], name="unique_product_cart"
            ),
        ]
        ordering = ["date_added"]

    @property
    def services(self) -> "QuerySet[CartProductAddService]":
        """Returns all add-on service links for this cart item."""
        return self._cart_product_add_services.all()

    @property
    def active_services(self) -> "QuerySet[CartProductAddService]":
        """Returns only active add-on services for this cart item."""
        return self.services.filter(active=True)


class CartProductAddService(models.Model):
    """Link between a cart item and a selectable add-on service."""

    cart_product = models.ForeignKey(
        "CartProduct",
        on_delete=models.CASCADE,
        related_name="_cart_product_add_services",
        verbose_name="Cart item",
    )
    service = models.ForeignKey(
        "store.ProductAddService",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Add-on service",
    )
    active = models.BooleanField(default=True, verbose_name="Selected?")

    class Meta:
        ordering = ["service__type"]
