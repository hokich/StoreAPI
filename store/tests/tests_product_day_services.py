from django.test import TestCase
from django.utils import timezone

from utils.exceptions import ObjectDoesNotExistException

from ..models import Brand, Listing, Product, ProductDay
from ..services.product_day import (
    PRODUCT_DAY_CATEGORIES,
    create_product_day,
    set_products_day_today,
)


class ProductDayTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для продукта, листинга и бренда
        self.listing = Listing.objects.create(
            name="Телевизоры",
            # Убедимся, что slug совпадает с ожидаемыми данными для тестов
            slug=PRODUCT_DAY_CATEGORIES[0],
        )
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.product = Product.objects.create(
            name="Test Product-1",
            slug="test-product-1",
            sku="test-sk1",
            price=4000.00,
            quantity=20,
            publish=True,
        )
        self.product._tags.set([self.listing, self.brand])

    def test_create_product_day_success(self) -> None:
        """Тест успешного создания товара дня"""
        date_now = timezone.now()
        product_day = create_product_day(self.product.id, date_now)
        self.assertIsNotNone(product_day)
        self.assertEqual(product_day.product, self.product)
        self.assertEqual(product_day.show_date, date_now.date())

    def test_create_product_day_with_non_existent_product(self) -> None:
        """Тест создания товара дня для несуществующего продукта"""
        date = timezone.now()
        with self.assertRaises(ObjectDoesNotExistException):
            create_product_day(9999, date)  # Несуществующий ID продукта

    def test_set_products_day_today_success(self) -> None:
        """Тест успешной установки товаров дня на сегодня"""
        # Создаем дополнительные продукты для теста
        for i in range(2, 12):
            product = Product.objects.create(
                name=f"Test Product {i}",
                slug=f"test-product-{i}",
                sku=f"test-sku-{i}",
                price=4000.00,
                quantity=30 - i,
                publish=True,
            )
            product._tags.set([self.listing, self.brand])

        set_products_day_today()
        products_day = ProductDay.objects.all()
        self.assertEqual(products_day.count(), 10)
        for product_day in products_day:
            self.assertTrue(product_day.product.price >= 3000)
            self.assertTrue(product_day.product.publish)
            self.assertIn(self.listing, product_day.product._tags.all())
            self.assertEqual(product_day.show_date, timezone.now().date())

    def test_clean_products_day(self) -> None:
        """Тест очистки существующих товаров дня"""
        create_product_day(self.product.id, timezone.now())
        ProductDay.clean_products_day()
        products_day = ProductDay.objects.all()
        self.assertFalse(products_day.exists())
