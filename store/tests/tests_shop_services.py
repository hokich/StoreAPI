from datetime import time

from django.test import TestCase

from store.models import Brand, Listing, Product, Shop
from store.services.shop import create_product_in_shop
from utils.exceptions import InvalidDataException, ObjectDoesNotExistException


class CreateProductInShopTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для продукта, листинга и бренда
        self.listing = Listing.objects.create(
            name="Test Listing", slug="test-listing"
        )
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="test-sku",
            price=1000.00,
        )
        self.product._tags.set([self.listing, self.brand])

        self.shop = Shop.objects.create(
            code="test-shop",
            name="Test Shop",
            working_from=time(8, 0, 0),
            working_to=time(20, 0, 0),
        )

    def test_create_product_in_shop_success(self) -> None:
        """Тест успешного создания товара в магазине"""
        product_in_shop = create_product_in_shop(
            self.product.id, self.shop.id, quantity=10
        )
        self.assertIsNotNone(product_in_shop)
        self.assertEqual(product_in_shop.product, self.product)
        self.assertEqual(product_in_shop.shop, self.shop)
        self.assertEqual(product_in_shop.quantity, 10)

    def test_create_product_in_shop_with_non_existent_product(self) -> None:
        """Тест создания товара в магазине для несуществующего продукта"""
        with self.assertRaises(ObjectDoesNotExistException):
            create_product_in_shop(
                9999, self.shop.id, quantity=10
            )  # Несуществующий ID продукта

    def test_create_product_in_shop_with_non_existent_shop(self) -> None:
        """Тест создания товара в несуществующем магазине"""
        with self.assertRaises(ObjectDoesNotExistException):
            create_product_in_shop(
                self.product.id, 9999, quantity=10
            )  # Несуществующий ID магазина

    def test_create_product_in_shop_with_invalid_quantity(self) -> None:
        """Тест создания товара в магазине с недопустимым количеством"""
        with self.assertRaises(InvalidDataException):
            # Недопустимое количество
            create_product_in_shop(self.product.id, self.shop.id, quantity=-5)
