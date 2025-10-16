from unittest.mock import Mock, patch

from django.test import TestCase

from utils.exceptions import (
    ObjectAlreadyExistsException,
    ObjectDoesNotExistException,
)

from ..models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Brand,
    FreeTag,
    Listing,
    Product,
    ProductAddService,
    ProductAttribute,
    Selection,
)
from ..services.product import (
    CreateProductDict,
    UpdateProductDict,
    _get_slug_by_name,
    _set_brand_in_product_attribute,
    create_product,
    set_product_add_services,
    update_product,
)


class SetBrandInProductAttributeTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для продукта и атрибута бренда
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="test-sku",
            price=1000.00,
        )

        self.brand_attribute = Attribute.objects.create(
            group=AttributeGroup.objects.create(name="Основные"),
            name="Бренд",
            slug="brend",
            type=Attribute.AttributeType.SELECT,
        )

    def test_set_brand_in_product_attribute_success(self) -> None:
        """Тест успешной установки бренда в атрибут продукта"""
        brand_name = "Apple"

        _set_brand_in_product_attribute(self.product, brand_name)

        product_attr = ProductAttribute.objects.filter(
            product=self.product, attribute=self.brand_attribute
        ).first()

        self.assertIsNotNone(product_attr)
        self.assertEqual(product_attr.values.first().value, brand_name)

    def test_set_brand_in_product_attribute_creates_new_attribute(
        self,
    ) -> None:
        """Тест создания нового атрибута продукта, если его еще нет"""
        brand_name = "Test Brand"

        _set_brand_in_product_attribute(self.product, brand_name)

        product_attr = ProductAttribute.objects.filter(
            product=self.product, attribute=self.brand_attribute
        ).first()

        self.assertIsNotNone(product_attr)
        self.assertEqual(product_attr.values.first().value, brand_name)

    def test_set_brand_in_product_attribute_creates_new_value(self) -> None:
        """Тест создания нового значения атрибута, если оно не существует"""
        brand_name = "New Brand"

        _set_brand_in_product_attribute(self.product, brand_name)

        attr_value = AttributeValue.objects.filter(value=brand_name).first()

        self.assertIsNotNone(attr_value)
        self.assertEqual(attr_value.value, brand_name)

    def test_set_brand_in_product_attribute_existing_value(self) -> None:
        """Тест установки существующего значения атрибута"""
        brand_name = "Existing Brand"
        existing_value = AttributeValue.objects.create(
            value=brand_name, slug="existing-brand"
        )

        _set_brand_in_product_attribute(self.product, brand_name)

        product_attr = ProductAttribute.objects.filter(
            product=self.product, attribute=self.brand_attribute
        ).first()

        self.assertIsNotNone(product_attr)
        self.assertIn(existing_value, product_attr.values.all())


class CreateProductTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для листинга и бренда
        self.listing = Listing.objects.create(
            name="Test Listing", slug="test-listing"
        )
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.selection = Selection.objects.create(
            name="Test Selection", slug="test-selection"
        )
        self.free_tag = FreeTag.objects.create(
            name="Test FreeTag", slug="test-freetag"
        )
        self.brand_attribute = Attribute.objects.create(
            group=AttributeGroup.objects.create(name="Основные"),
            name="Бренд",
            slug="brend",
            type=Attribute.AttributeType.SELECT,
        )

    def test_create_product_success(self) -> None:
        """Тест успешного создания продукта"""
        product_data = CreateProductDict(
            name="Test Product",
            sku="test-sku",
            price=100.00,
            listing_id=self.listing.id,
            brand_id=self.brand.id,
            short_description="Test Description",
            quantity=10,
            discount_percent=10.0,
            model="Test Model",
            youtube_link="https://youtube.com/test",
            bonuses=True,
            publish=True,
            other_tags_ids=[self.selection.id, self.free_tag.id],
        )
        product = create_product(product_data)
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.sku, "test-sku")
        self.assertEqual(product.price, 100.00)
        self.assertEqual(product.short_description, "Test Description")
        self.assertEqual(product.quantity, 10)
        self.assertEqual(product.discount_percent, 10.0)
        self.assertEqual(product.model, "Test Model")
        self.assertEqual(product.youtube_link, "https://youtube.com/test")
        self.assertTrue(product.bonuses)
        self.assertTrue(product.publish)
        self.assertEqual(
            set(product._tags.all()),
            {self.listing, self.brand, self.selection, self.free_tag},
        )

    def test_create_product_with_existing_sku(self) -> None:
        """Тест создания продукта с уже существующим SKU"""
        Product.objects.create(
            name="Existing Product",
            slug="existing-slug",
            sku="existing-sku",
            price=100.00,
        )
        product_data = CreateProductDict(
            name="New Product",
            sku="existing-sku",
            price=100.00,
            listing_id=self.listing.id,
            brand_id=self.brand.id,
        )
        with self.assertRaises(ObjectAlreadyExistsException):
            create_product(product_data)

    def test_create_product_with_non_existent_listing(self) -> None:
        """Тест создания продукта с несуществующим листингом"""
        product_data = CreateProductDict(
            name="Test Product",
            sku="test-sku",
            price=100.00,
            listing_id=9999,  # Несуществующий ID листинга
            brand_id=self.brand.id,
        )
        with self.assertRaises(ObjectDoesNotExistException):
            create_product(product_data)

    def test_create_product_with_non_existent_brand(self) -> None:
        """Тест создания продукта с несуществующим брендом"""
        product_data = CreateProductDict(
            name="Test Product",
            sku="test-sku",
            price=100.00,
            listing_id=self.listing.id,
            brand_id=9999,  # Несуществующий ID бренда
        )
        with self.assertRaises(ObjectDoesNotExistException):
            create_product(product_data)

    def test_create_product_with_non_existent_other_tags(self) -> None:
        """Тест создания продукта с несуществующими дополнительными тегами"""
        product_data = CreateProductDict(
            name="Test Product",
            sku="test-sku",
            price=100.00,
            listing_id=self.listing.id,
            brand_id=self.brand.id,
            other_tags_ids=[9999],  # Несуществующий ID тега
        )
        with self.assertRaises(ObjectDoesNotExistException):
            create_product(product_data)


class UpdateProductTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для продукта, листинга, бренда, выборки и свободного тега
        self.listing = Listing.objects.create(
            name="Test Listing", slug="test-listing"
        )
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.selection = Selection.objects.create(
            name="Test Selection", slug="test-selection"
        )
        self.free_tag = FreeTag.objects.create(
            name="Test FreeTag", slug="test-freetag"
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="test-sku",
            price=100.00,
        )
        self.product._tags.set([self.listing, self.brand])
        self.brand_attribute = Attribute.objects.create(
            group=AttributeGroup.objects.create(name="Основные"),
            name="Бренд",
            slug="brend",
            type=Attribute.AttributeType.SELECT,
        )

    def test_update_product_success(self) -> None:
        """Тест успешного обновления продукта"""
        update_data = UpdateProductDict(
            name="Updated Product",
            sku="updated-sku",
            price=150.00,
            listing_id=self.listing.id,
            brand_id=self.brand.id,
            short_description="Updated Description",
            quantity=20,
            discount_percent=20.0,
            model="Updated Model",
            youtube_link="https://youtube.com/updated",
            bonuses=False,
            publish=False,
            other_tags_ids=[self.selection.id, self.free_tag.id],
        )
        updated_product = update_product(
            product_id=self.product.id, product_data=update_data
        )
        self.assertIsNotNone(updated_product)
        self.assertEqual(updated_product.name, "Updated Product")
        self.assertEqual(updated_product.sku, "updated-sku")
        self.assertEqual(updated_product.price, 150.00)
        self.assertEqual(
            updated_product.short_description, "Updated Description"
        )
        self.assertEqual(updated_product.quantity, 20)
        self.assertEqual(updated_product.discount_percent, 20.0)
        self.assertEqual(updated_product.model, "Updated Model")
        self.assertEqual(
            updated_product.youtube_link, "https://youtube.com/updated"
        )
        self.assertFalse(updated_product.bonuses)
        self.assertFalse(updated_product.publish)
        self.assertEqual(
            set(updated_product._tags.all()),
            {self.listing, self.brand, self.selection, self.free_tag},
        )

    def test_update_product_with_non_existent_product(self) -> None:
        """Тест обновления несуществующего продукта"""
        update_data = UpdateProductDict(
            name="Non-existent Product",
            sku="non-existent-sku",
            price=150.00,
            listing_id=self.listing.id,
            brand_id=self.brand.id,
            short_description=None,
            quantity=None,
            discount_percent=None,
            model=None,
            youtube_link=None,
            bonuses=False,
            publish=True,
            other_tags_ids=[],
        )
        with self.assertRaises(ObjectDoesNotExistException):
            update_product(
                product_id=9999, product_data=update_data
            )  # Несуществующий ID продукта

    def test_update_product_with_existing_sku(self) -> None:
        """Тест обновления продукта с уже существующим SKU"""
        Product.objects.create(
            name="Existing Product",
            slug="existing-slug",
            sku="existing-sku",
            price=100.00,
        )
        update_data = UpdateProductDict(
            name="Updated Product",
            sku="existing-sku",
            price=150.00,
            listing_id=self.listing.id,
            brand_id=self.brand.id,
            short_description=None,
            quantity=None,
            discount_percent=None,
            model=None,
            youtube_link=None,
            bonuses=False,
            publish=True,
            other_tags_ids=[],
        )
        with self.assertRaises(ObjectAlreadyExistsException):
            update_product(
                product_id=self.product.id, product_data=update_data
            )

    def test_update_product_with_non_existent_listing(self) -> None:
        """Тест обновления продукта с несуществующим листингом"""
        update_data = UpdateProductDict(
            name="Updated Product",
            sku="updated-sku",
            price=150.00,
            listing_id=9999,  # Несуществующий ID листинга
            brand_id=self.brand.id,
            short_description=None,
            quantity=None,
            discount_percent=None,
            model=None,
            youtube_link=None,
            bonuses=False,
            publish=True,
            other_tags_ids=[],
        )
        with self.assertRaises(ObjectDoesNotExistException):
            update_product(
                product_id=self.product.id, product_data=update_data
            )

    def test_update_product_with_non_existent_brand(self) -> None:
        """Тест обновления продукта с несуществующим брендом"""
        update_data = UpdateProductDict(
            name="Updated Product",
            sku="updated-sku",
            price=150.00,
            listing_id=self.listing.id,
            brand_id=9999,  # Несуществующий ID бренда,
            short_description=None,
            quantity=None,
            discount_percent=None,
            model=None,
            youtube_link=None,
            bonuses=False,
            publish=True,
            other_tags_ids=[],
        )
        with self.assertRaises(ObjectDoesNotExistException):
            update_product(
                product_id=self.product.id, product_data=update_data
            )

    def test_update_product_with_non_existent_other_tags(self) -> None:
        """Тест обновления продукта с несуществующими дополнительными тегами"""

        update_data = UpdateProductDict(
            name="Updated Product",
            sku="updated-sku",
            price=150.00,
            listing_id=self.listing.id,
            brand_id=self.brand.id,
            short_description=None,
            quantity=None,
            discount_percent=None,
            model=None,
            youtube_link=None,
            bonuses=False,
            publish=True,
            other_tags_ids=[9999],
        )

        with self.assertRaises(ObjectDoesNotExistException):
            update_product(
                product_id=self.product.id, product_data=update_data
            )


class GetSlugByNameTests(TestCase):

    def test_generate_slug_for_new_name(self) -> None:
        """Тест генерации slug для нового имени продукта"""
        name = "Продукт Новый"
        expected_slug = "produkt-novyj"
        slug = _get_slug_by_name(name)
        self.assertEqual(slug, expected_slug)

    @patch(
        "store.services.product._check_product_exists_by_slug",
        return_value=True,
    )
    def test_generate_unique_slug(
        self, mock_check_product_exists_by_slug: Mock
    ) -> None:
        """Тест генерации уникального slug, если такой уже существует"""
        mock_check_product_exists_by_slug.side_effect = [
            True,  # Существует первый slug
            False,  # Второй slug уникален
        ]
        name = "Продукт Новый"
        slug = _get_slug_by_name(name)
        self.assertEqual(slug, "produkt-novyj-1")

    def test_translit_correctness(self) -> None:
        """Тест корректности транслитерации названия продукта"""
        name = "Продукт Ёж"
        expected_slug = "produkt-yozh"
        slug = _get_slug_by_name(name)
        self.assertEqual(slug, expected_slug)


class SetProductAddServicesTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для продукта, листинга и атрибутов
        self.listing = Listing.objects.create(
            name="Test Listing",
            slug="televizory",  # Убедимся, что slug совпадает с ожидаемыми данными для тестов
        )
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="test-sku",
            price=1000.00,
        )
        self.product._tags.set([self.listing, self.brand])

        self.attribute_group = AttributeGroup.objects.create(name="Test Group")
        self.diagonal_attribute = Attribute.objects.create(
            group=self.attribute_group,
            name="Diagonal",
            slug="diagonal",
            type=Attribute.AttributeType.NUM_INT,
        )
        self.diagonal_value = AttributeValue.objects.create(
            value="32", slug="32"
        )
        self.product_attribute = ProductAttribute.objects.create(
            product=self.product, attribute=self.diagonal_attribute
        )
        self.product_attribute._values.set([self.diagonal_value])

    def test_set_product_add_services_success(self) -> None:
        """Тест успешного добавления дополнительных услуг для продукта"""
        set_product_add_services(self.product.id)
        services = ProductAddService.objects.filter(product=self.product)
        self.assertTrue(services.exists())
        for service in services:
            self.assertIn(service.type, ProductAddService.ServiceType.values)
            self.assertGreater(service.price, 0)

    def test_set_product_add_services_warranty(self) -> None:
        """Тест добавления услуги 'Гарантия' для продукта"""
        set_product_add_services(self.product.id)
        services = ProductAddService.objects.filter(
            product=self.product, type=ProductAddService.ServiceType.WARRANTY
        )
        self.assertTrue(services.exists())
        for service in services:
            self.assertIn("года", service.name)
            self.assertGreater(service.price, 0)

    def test_set_product_add_services_installing(self) -> None:
        """Тест добавления услуги 'Установка' для продукта"""
        set_product_add_services(self.product.id)
        services = ProductAddService.objects.filter(
            product=self.product, type=ProductAddService.ServiceType.INSTALLING
        )
        self.assertTrue(services.exists())
        for service in services:
            self.assertEqual(service.name, "Старт-мастер")
            self.assertGreater(service.price, 0)

    def test_set_product_add_services_setting_up(self) -> None:
        """Тест добавления услуги 'Настройка' для продукта"""
        set_product_add_services(self.product.id)
        services = ProductAddService.objects.filter(
            product=self.product, type=ProductAddService.ServiceType.SETTING_UP
        )
        self.assertTrue(services.exists())
        for service in services:
            self.assertIn("Фокс-мастер", service.name)
            self.assertGreater(service.price, 0)

    def test_set_product_add_services_with_non_existent_product(self) -> None:
        """Тест установки дополнительных услуг для несуществующего продукта"""
        with self.assertRaises(ObjectDoesNotExistException):
            set_product_add_services(9999)  # Несуществующий ID продукта
