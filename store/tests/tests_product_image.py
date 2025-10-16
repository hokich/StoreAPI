import os

from django.test import TestCase
from PIL import Image as PilImage

from images.models import Image
from utils.exceptions import ObjectDoesNotExistException
from utils.for_tests import create_test_image

from ..models import Brand, Listing, Product, ProductImage
from ..services.product_image import (
    create_product_image,
    delete_product_image,
    set_main_product_image,
)


class CreateProductImageTests(TestCase):

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

        self.image_file = create_test_image()

        self.created_images: list[str] = []

    def tearDown(self) -> None:
        # Удаляем созданные файлы изображений после тестов
        for image_path in self.created_images:
            if os.path.exists(image_path):
                os.remove(image_path)

    def test_create_product_image_success(self) -> None:
        """Тест успешного создания изображения товара"""
        product_image = create_product_image(
            self.product.id, self.image_file, is_main=True
        )
        self.assertIsNotNone(product_image)
        self.assertEqual(product_image.product, self.product)
        self.assertTrue(product_image.is_main)

        # Проверка созданных изображений
        self.assertTrue(isinstance(product_image.thumb_image, Image))
        self.assertTrue(isinstance(product_image.sd_image, Image))
        self.assertTrue(isinstance(product_image.hd_image, Image))

        # Записываем пути созданных изображений
        self.created_images.append(product_image.thumb_image.image.path)
        self.created_images.append(product_image.sd_image.image.path)
        self.created_images.append(product_image.hd_image.image.path)

    def test_create_product_image_with_non_existent_product(self) -> None:
        """Тест создания изображения товара для несуществующего продукта"""
        with self.assertRaises(ObjectDoesNotExistException):
            create_product_image(
                9999, self.image_file, is_main=True
            )  # Несуществующий ID продукта

    def test_create_product_image_multiple_sizes(self) -> None:
        """Тест создания изображения товара в нескольких размерах"""
        product_image = create_product_image(self.product.id, self.image_file)
        self.assertIsNotNone(product_image)

        # Проверка размеров изображений
        thumb_image_path = product_image.thumb_image.image.path
        sd_image_path = product_image.sd_image.image.path
        hd_image_path = product_image.hd_image.image.path

        thumb_image = PilImage.open(thumb_image_path)
        sd_image = PilImage.open(sd_image_path)
        hd_image = PilImage.open(hd_image_path)

        self.assertLessEqual(thumb_image.width, 768)
        self.assertLessEqual(thumb_image.height, 768)
        self.assertLessEqual(sd_image.width, 1024)
        self.assertLessEqual(sd_image.height, 1024)
        self.assertLessEqual(hd_image.width, 1920)
        self.assertLessEqual(hd_image.height, 1920)

        # Записываем пути созданных изображений
        self.created_images.append(thumb_image_path)
        self.created_images.append(sd_image_path)
        self.created_images.append(hd_image_path)


class DeleteProductImageTests(TestCase):

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

        self.image_file = create_test_image()

        self.created_images: list[str] = []

    def test_delete_product_image_success(self) -> None:
        """Тест успешного удаления изображения товара"""
        product_image = create_product_image(
            self.product.id, self.image_file, is_main=True
        )

        # Записываем пути созданных изображений
        self.created_images.append(product_image.thumb_image.image.path)
        self.created_images.append(product_image.sd_image.image.path)
        self.created_images.append(product_image.hd_image.image.path)

        product_image_id = product_image.id

        # Удаляем изображение товара
        delete_product_image(product_image_id)

        # Проверяем, что изображение товара и связанные файлы были удалены
        with self.assertRaises(ObjectDoesNotExistException):
            ProductImage.get_product_image_by_pk(product_image_id)

        for image_path in self.created_images:
            self.assertFalse(os.path.exists(image_path))

    def test_delete_product_image_with_non_existent_product_image(
        self,
    ) -> None:
        """Тест удаления несуществующего изображения товара"""
        with self.assertRaises(ObjectDoesNotExistException):
            delete_product_image(9999)  # Несуществующий ID изображения товара


class SetMainProductImageTests(TestCase):

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

        self.image_file = create_test_image()

        self.created_images: list[str] = []

    def tearDown(self) -> None:
        # Удаляем созданные файлы изображений после тестов
        for image_path in self.created_images:
            if os.path.exists(image_path):
                os.remove(image_path)

    def test_set_main_product_image_success(self) -> None:
        """Тест успешной установки изображения товара в качестве основного"""
        product_image = create_product_image(
            self.product.id, self.image_file, is_main=False
        )

        # Записываем пути созданных изображений
        self.created_images.append(product_image.thumb_image.image.path)
        self.created_images.append(product_image.sd_image.image.path)
        self.created_images.append(product_image.hd_image.image.path)

        set_main_product_image(product_image.id)

        updated_product_image = ProductImage.get_product_image_by_pk(
            product_image.id
        )
        self.assertTrue(updated_product_image.is_main)

    def test_set_main_product_image_with_existing_main_image(self) -> None:
        """Тест установки изображения товара в качестве основного, когда уже есть основное изображение"""
        product_image1 = create_product_image(
            self.product.id, self.image_file, is_main=True
        )

        # Записываем пути созданных изображений
        self.created_images.append(product_image1.thumb_image.image.path)
        self.created_images.append(product_image1.sd_image.image.path)
        self.created_images.append(product_image1.hd_image.image.path)

        product_image2 = create_product_image(
            self.product.id, self.image_file, is_main=False
        )

        # Записываем пути созданных изображений
        self.created_images.append(product_image2.thumb_image.image.path)
        self.created_images.append(product_image2.sd_image.image.path)
        self.created_images.append(product_image2.hd_image.image.path)

        set_main_product_image(product_image2.id)

        updated_product_image1 = ProductImage.get_product_image_by_pk(
            product_image1.id
        )
        updated_product_image2 = ProductImage.get_product_image_by_pk(
            product_image2.id
        )

        self.assertFalse(updated_product_image1.is_main)
        self.assertTrue(updated_product_image2.is_main)

    def test_set_main_product_image_with_non_existent_image(self) -> None:
        """Тест установки несуществующего изображения товара в качестве основного"""
        with self.assertRaises(ObjectDoesNotExistException):
            set_main_product_image(
                9999
            )  # Несуществующий ID изображения товара
