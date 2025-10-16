from django.test import TestCase

from utils.exceptions import (
    ObjectAlreadyExistsException,
    ObjectDoesNotExistException,
)

from ..models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Listing,
    ListingAttribute,
    Product,
    ProductAttribute,
)
from ..services.attribute import (
    UpdateAttributeDict,
    _check_attribute_exists_by_name,
    _check_attribute_exists_by_slug,
    _check_attribute_value_exists_by_slug,
    _check_attribute_value_exists_by_value,
    _get_attribute_slug_by_name,
    _get_attribute_value_slug_by_value,
    create_attribute,
    create_attribute_group,
    create_attribute_value,
    create_listing_attribute,
    create_product_attribute,
    set_listing_attribute_values,
    set_product_attribute_values,
    update_attribute,
    update_attribute_group,
    update_attribute_value,
)


class CreateAttributeGroupTests(TestCase):

    def test_create_attribute_group_success(self) -> None:
        """Тест успешного создания группы атрибутов"""
        group_name = "Test Group"
        attribute_group = create_attribute_group(name=group_name)
        self.assertIsNotNone(attribute_group)
        self.assertEqual(attribute_group.name, group_name)

    def test_create_attribute_group_with_existing_name(self) -> None:
        """Тест создания группы атрибутов с уже существующим именем"""
        group_name = "Existing Group"
        AttributeGroup.objects.create(name=group_name)

        with self.assertRaises(ObjectAlreadyExistsException):
            create_attribute_group(name=group_name)


class UpdateAttributeGroupTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для группы атрибутов
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")

    def test_update_attribute_group_success(self) -> None:
        """Тест успешного обновления группы атрибутов"""
        new_name = "Updated Group"
        updated_group = update_attribute_group(
            group_id=self.attribute_group.id, new_name=new_name
        )
        self.assertIsNotNone(updated_group)
        self.assertEqual(updated_group.name, new_name)

    def test_update_attribute_group_with_existing_name(self) -> None:
        """Тест обновления группы атрибутов с уже существующим именем"""
        existing_group_name = "Existing Group"
        AttributeGroup.objects.create(name=existing_group_name)

        with self.assertRaises(ObjectAlreadyExistsException):
            update_attribute_group(
                group_id=self.attribute_group.id, new_name=existing_group_name
            )

    def test_update_attribute_group_non_existent(self) -> None:
        """Тест обновления несуществующей группы атрибутов"""
        non_existent_group_id = 9999
        with self.assertRaises(ObjectDoesNotExistException):
            update_attribute_group(
                group_id=non_existent_group_id, new_name="New Name"
            )


class AttributeUtilsTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовую группу атрибутов
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")
        # Создаем тестовый атрибут
        self.attribute = Attribute.objects.create(
            group=self.attribute_group,
            name="Test Attribute",
            slug="test-attribute",
            type=Attribute.AttributeType.TEXT,
        )

    def test_get_attribute_slug_by_name_unique(self) -> None:
        """Тест получения уникального slug для нового атрибута"""
        new_name = "New Attribute"
        slug = _get_attribute_slug_by_name(new_name)
        self.assertEqual(slug, "new-attribute")

    def test_get_attribute_slug_by_name_duplicate(self) -> None:
        """Тест получения уникального slug при дублировании названия"""
        duplicate_name = "Test Attribute"
        slug = _get_attribute_slug_by_name(duplicate_name)
        self.assertNotEqual(slug, "test-attribute")
        self.assertTrue(slug.startswith("test-attribute"))

    def test_check_attribute_exists_by_slug_exists(self) -> None:
        """Тест проверки существования атрибута по его slug (существует)"""
        exists = _check_attribute_exists_by_slug("test-attribute")
        self.assertTrue(exists)

    def test_check_attribute_exists_by_slug_not_exists(self) -> None:
        """Тест проверки существования атрибута по его slug (не существует)"""
        exists = _check_attribute_exists_by_slug("non-existent-slug")
        self.assertFalse(exists)

    def test_check_attribute_exists_by_name_exists(self) -> None:
        """Тест проверки существования атрибута по его имени (существует)"""
        exists = _check_attribute_exists_by_name("Test Attribute")
        self.assertTrue(exists)

    def test_check_attribute_exists_by_name_not_exists(self) -> None:
        """Тест проверки существования атрибута по его имени (не существует)"""
        exists = _check_attribute_exists_by_name("Non-existent Attribute")
        self.assertFalse(exists)


class CreateAttributeTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовую группу атрибутов
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")

    def test_create_attribute_success(self) -> None:
        """Тест успешного создания атрибута"""
        attribute = create_attribute(
            group_id=self.attribute_group.id,
            name="Test Attribute",
            attribute_type=str(Attribute.AttributeType.TEXT),
            slug="test-attribute",
            added_name="Added Name",
            measure_unit="kg",
            visibility_in_filter=True,
        )
        self.assertIsNotNone(attribute)
        self.assertEqual(attribute.name, "Test Attribute")
        self.assertEqual(attribute.type, Attribute.AttributeType.TEXT)
        self.assertEqual(attribute.slug, "test-attribute")
        self.assertEqual(attribute.added_name, "Added Name")
        self.assertEqual(attribute.measure_unit, "kg")
        self.assertTrue(attribute.visibility_in_filter)

    def test_create_attribute_with_invalid_type(self) -> None:
        """Тест создания атрибута с недопустимым типом"""
        with self.assertRaises(ValueError):
            create_attribute(
                group_id=self.attribute_group.id,
                name="Invalid Attribute",
                attribute_type="INVALID_TYPE",
            )

    def test_create_attribute_with_existing_name(self) -> None:
        """Тест создания атрибута с уже существующим именем"""
        Attribute.objects.create(
            group=self.attribute_group,
            name="Existing Attribute",
            slug="existing-attribute",
            type=str(Attribute.AttributeType.TEXT),
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_attribute(
                group_id=self.attribute_group.id,
                name="Existing Attribute",
                attribute_type=str(Attribute.AttributeType.TEXT),
            )

    def test_create_attribute_with_existing_slug(self) -> None:
        """Тест создания атрибута с уже существующим slug"""
        Attribute.objects.create(
            group=self.attribute_group,
            name="Unique Attribute",
            slug="existing-slug",
            type=str(Attribute.AttributeType.TEXT),
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_attribute(
                group_id=self.attribute_group.id,
                name="Another Attribute",
                attribute_type=str(Attribute.AttributeType.TEXT),
                slug="existing-slug",
            )


class UpdateAttributeTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для группы атрибутов и атрибута
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")
        self.attribute = Attribute.objects.create(
            group=self.attribute_group,
            name="Test Attribute",
            slug="test-attribute",
            type=Attribute.AttributeType.TEXT,
        )

    def test_update_attribute_success(self) -> None:
        """Тест успешного обновления атрибута"""
        updated_data = UpdateAttributeDict(
            group_id=self.attribute_group.id,
            name="Updated Attribute",
            attribute_type=str(Attribute.AttributeType.NUM_INT),
            slug="updated-attribute",
            added_name="Updated Name",
            measure_unit="cm",
            visibility_in_filter=True,
        )

        updated_attribute = update_attribute(
            attribute_id=self.attribute.id, attribute_data=updated_data
        )
        self.assertIsNotNone(updated_attribute)
        self.assertEqual(updated_attribute.name, "Updated Attribute")
        self.assertEqual(
            updated_attribute.type, Attribute.AttributeType.NUM_INT
        )
        self.assertEqual(updated_attribute.slug, "updated-attribute")
        self.assertEqual(updated_attribute.added_name, "Updated Name")
        self.assertEqual(updated_attribute.measure_unit, "cm")
        self.assertTrue(updated_attribute.visibility_in_filter)

    def test_update_attribute_with_invalid_type(self) -> None:
        """Тест обновления атрибута с недопустимым типом"""
        updated_data = UpdateAttributeDict(
            group_id=self.attribute_group.id,
            name="Invalid Attribute",
            attribute_type="INVALID_TYPE",
            slug="invalid-attribute",
            added_name="Invalid Name",
            measure_unit="kg",
            visibility_in_filter=False,
        )

        with self.assertRaises(ValueError):
            update_attribute(
                attribute_id=self.attribute.id, attribute_data=updated_data
            )

    def test_update_attribute_with_existing_name(self) -> None:
        """Тест обновления атрибута с уже существующим именем"""
        Attribute.objects.create(
            group=self.attribute_group,
            name="Existing Attribute",
            slug="existing-attribute",
            type=str(Attribute.AttributeType.TEXT),
        )

        updated_data = UpdateAttributeDict(
            group_id=self.attribute_group.id,
            name="Existing Attribute",
            attribute_type=str(Attribute.AttributeType.TEXT),
            slug="updated-slug",
            added_name="Updated Name",
            measure_unit="kg",
            visibility_in_filter=False,
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            update_attribute(
                attribute_id=self.attribute.id, attribute_data=updated_data
            )

    def test_update_attribute_with_existing_slug(self) -> None:
        """Тест обновления атрибута с уже существующим slug"""
        Attribute.objects.create(
            group=self.attribute_group,
            name="Unique Attribute",
            slug="existing-slug",
            type=str(Attribute.AttributeType.TEXT),
        )

        updated_data = UpdateAttributeDict(
            group_id=self.attribute_group.id,
            name="Another Attribute",
            attribute_type=str(Attribute.AttributeType.TEXT),
            slug="existing-slug",
            added_name="Updated Name",
            measure_unit="kg",
            visibility_in_filter=False,
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            update_attribute(
                attribute_id=self.attribute.id, attribute_data=updated_data
            )


class CreateAttributeValueTests(TestCase):

    def test_create_attribute_value_success(self) -> None:
        """Тест успешного создания значения атрибута"""
        value = "Test Value"
        attribute_value = create_attribute_value(
            value=value, slug="test-value"
        )
        self.assertIsNotNone(attribute_value)
        self.assertEqual(attribute_value.value, value)
        self.assertEqual(attribute_value.slug, "test-value")

    def test_create_attribute_value_with_generated_slug(self) -> None:
        """Тест успешного создания значения атрибута с автоматически сгенерированным slug"""
        value = "Generated Slug Value"
        attribute_value = create_attribute_value(value=value)
        self.assertIsNotNone(attribute_value)
        self.assertEqual(attribute_value.value, value)
        self.assertTrue(
            attribute_value.slug.startswith("generated-slug-value")
        )

    def test_create_attribute_value_with_existing_value(self) -> None:
        """Тест создания значения атрибута с уже существующим значением"""
        AttributeValue.objects.create(
            value="Existing Value", slug="existing-value"
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_attribute_value(value="Existing Value")

    def test_create_attribute_value_with_existing_slug(self) -> None:
        """Тест создания значения атрибута с уже существующим slug"""
        AttributeValue.objects.create(
            value="Unique Value", slug="existing-slug"
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_attribute_value(value="Another Value", slug="existing-slug")


class UpdateAttributeValueTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для значения атрибута
        self.attribute_value = AttributeValue.objects.create(
            value="Test Value", slug="test-value"
        )

    def test_update_attribute_value_success(self) -> None:
        """Тест успешного обновления значения атрибута"""
        new_value = "Updated Value"
        new_slug = "updated-value"
        updated_value = update_attribute_value(
            value_id=self.attribute_value.id,
            new_value=new_value,
            new_slug=new_slug,
        )
        self.assertIsNotNone(updated_value)
        self.assertEqual(updated_value.value, new_value)
        self.assertEqual(updated_value.slug, new_slug)

    def test_update_attribute_value_with_existing_value(self) -> None:
        """Тест обновления значения атрибута с уже существующим значением"""
        AttributeValue.objects.create(
            value="Existing Value", slug="existing-value"
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            update_attribute_value(
                value_id=self.attribute_value.id, new_value="Existing Value"
            )

    def test_update_attribute_value_with_existing_slug(self) -> None:
        """Тест обновления значения атрибута с уже существующим slug"""
        AttributeValue.objects.create(
            value="Unique Value", slug="existing-slug"
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            update_attribute_value(
                value_id=self.attribute_value.id, new_slug="existing-slug"
            )

    def test_update_attribute_value_with_no_changes(self) -> None:
        """Тест обновления значения атрибута без изменений"""
        updated_value = update_attribute_value(
            value_id=self.attribute_value.id
        )
        self.assertIsNotNone(updated_value)
        self.assertEqual(updated_value.value, "Test Value")
        self.assertEqual(updated_value.slug, "test-value")


class AttributeValueUtilsTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для значения атрибута
        self.attribute_value = AttributeValue.objects.create(
            value="Test Value", slug="test-value"
        )

    def test_get_attribute_value_slug_by_value(self) -> None:
        """Тест получения slug на основе значения атрибута"""
        value = "New Value"
        slug = _get_attribute_value_slug_by_value(value)
        self.assertEqual(slug, "new-value")

    def test_check_attribute_value_exists_by_slug_exists(self) -> None:
        """Тест проверки существования значения атрибута по его slug (существует)"""
        exists = _check_attribute_value_exists_by_slug("test-value")
        self.assertTrue(exists)

    def test_check_attribute_value_exists_by_slug_not_exists(self) -> None:
        """Тест проверки существования значения атрибута по его slug (не существует)"""
        exists = _check_attribute_value_exists_by_slug("non-existent-slug")
        self.assertFalse(exists)

    def test_check_attribute_value_exists_by_value_exists(self) -> None:
        """Тест проверки существования значения атрибута по его значению (существует)"""
        exists = _check_attribute_value_exists_by_value("Test Value")
        self.assertTrue(exists)

    def test_check_attribute_value_exists_by_value_not_exists(self) -> None:
        """Тест проверки существования значения атрибута по его значению (не существует)"""
        exists = _check_attribute_value_exists_by_value("Non-existent Value")
        self.assertFalse(exists)


class CreateProductAttributeTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для продукта и атрибута
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="test-sku",
            price=100.00,
        )
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")
        self.attribute = Attribute.objects.create(
            group=self.attribute_group,
            name="Test Attribute",
            slug="test-attribute",
            type=Attribute.AttributeType.TEXT,
        )
        self.attribute_value1 = AttributeValue.objects.create(
            value="Value 1", slug="value-1"
        )
        self.attribute_value2 = AttributeValue.objects.create(
            value="Value 2", slug="value-2"
        )

    def test_create_product_attribute_success(self) -> None:
        """Тест успешного создания атрибута продукта"""
        value_ids = [self.attribute_value1.id, self.attribute_value2.id]
        product_attribute = create_product_attribute(
            product_id=self.product.id,
            attribute_id=self.attribute.id,
            value_ids=value_ids,
        )
        self.assertIsNotNone(product_attribute)
        self.assertEqual(product_attribute.product, self.product)
        self.assertEqual(product_attribute.attribute, self.attribute)
        self.assertEqual(
            list(product_attribute._values.all()),
            [self.attribute_value1, self.attribute_value2],
        )

    def test_create_product_attribute_with_duplicate(self) -> None:
        """Тест создания дублирующего атрибута продукта"""
        create_product_attribute(
            product_id=self.product.id, attribute_id=self.attribute.id
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_product_attribute(
                product_id=self.product.id, attribute_id=self.attribute.id
            )

    def test_create_product_attribute_with_non_existent_value(self) -> None:
        """Тест создания атрибута продукта с несуществующим значением"""
        non_existent_value_id = 9999
        value_ids = [self.attribute_value1.id, non_existent_value_id]

        with self.assertRaises(ObjectDoesNotExistException):
            create_product_attribute(
                product_id=self.product.id,
                attribute_id=self.attribute.id,
                value_ids=value_ids,
            )


class SetProductAttributeValuesTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для продукта, атрибута и значений атрибута
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            sku="test-sku",
            price=100.00,
        )
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")
        self.attribute = Attribute.objects.create(
            group=self.attribute_group,
            name="Test Attribute",
            slug="test-attribute",
            type=Attribute.AttributeType.TEXT,
        )
        self.product_attribute = ProductAttribute.objects.create(
            product=self.product, attribute=self.attribute
        )
        self.attribute_value1 = AttributeValue.objects.create(
            value="Value 1", slug="value-1"
        )
        self.attribute_value2 = AttributeValue.objects.create(
            value="Value 2", slug="value-2"
        )

    def test_set_product_attribute_values_success(self) -> None:
        """Тест успешного обновления значений атрибута продукта"""
        value_ids = [self.attribute_value1.id, self.attribute_value2.id]
        updated_product_attribute = set_product_attribute_values(
            product_attribute_id=self.product_attribute.id, value_ids=value_ids
        )
        self.assertIsNotNone(updated_product_attribute)
        self.assertEqual(
            list(updated_product_attribute._values.all()),
            [self.attribute_value1, self.attribute_value2],
        )

    def test_set_product_attribute_values_with_non_existent_value(
        self,
    ) -> None:
        """Тест обновления значений атрибута продукта с несуществующим значением"""
        non_existent_value_id = 9999
        value_ids = [self.attribute_value1.id, non_existent_value_id]

        with self.assertRaises(ObjectDoesNotExistException):
            set_product_attribute_values(
                product_attribute_id=self.product_attribute.id,
                value_ids=value_ids,
            )


class CreateListingAttributeTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для листинга, атрибута и значений атрибута
        self.listing = Listing.objects.create(
            name="Test Listing", slug="test-listing"
        )
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")
        self.attribute = Attribute.objects.create(
            group=self.attribute_group,
            name="Test Attribute",
            slug="test-attribute",
            type=Attribute.AttributeType.TEXT,
        )
        self.attribute_value1 = AttributeValue.objects.create(
            value="Value 1", slug="value-1"
        )
        self.attribute_value2 = AttributeValue.objects.create(
            value="Value 2", slug="value-2"
        )

    def test_create_listing_attribute_success(self) -> None:
        """Тест успешного создания атрибута листинга"""
        value_ids = [self.attribute_value1.id, self.attribute_value2.id]
        listing_attribute = create_listing_attribute(
            listing_id=self.listing.id,
            attribute_id=self.attribute.id,
            value_ids=value_ids,
            order=1000,
        )
        self.assertIsNotNone(listing_attribute)
        self.assertEqual(listing_attribute.listing, self.listing)
        self.assertEqual(listing_attribute.attribute, self.attribute)
        self.assertEqual(listing_attribute.order, 1000)
        self.assertEqual(
            list(listing_attribute._possible_values.all()),
            [self.attribute_value1, self.attribute_value2],
        )

    def test_create_listing_attribute_with_duplicate(self) -> None:
        """Тест создания дублирующего атрибута листинга"""
        create_listing_attribute(
            listing_id=self.listing.id, attribute_id=self.attribute.id
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_listing_attribute(
                listing_id=self.listing.id, attribute_id=self.attribute.id
            )

    def test_create_listing_attribute_with_non_existent_value(self) -> None:
        """Тест создания атрибута листинга с несуществующим значением"""
        non_existent_value_id = 9999
        value_ids = [self.attribute_value1.id, non_existent_value_id]

        with self.assertRaises(ObjectDoesNotExistException):
            create_listing_attribute(
                listing_id=self.listing.id,
                attribute_id=self.attribute.id,
                value_ids=value_ids,
            )


class SetListingAttributeValuesTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для листинга, атрибута и значений атрибута
        self.listing = Listing.objects.create(
            name="Test Listing", slug="test-listing"
        )
        self.attribute_group = AttributeGroup.objects.create(name="Test Group")
        self.attribute = Attribute.objects.create(
            group=self.attribute_group,
            name="Test Attribute",
            slug="test-attribute",
            type=Attribute.AttributeType.TEXT,
        )
        self.listing_attribute = ListingAttribute.objects.create(
            listing=self.listing, attribute=self.attribute
        )
        self.attribute_value1 = AttributeValue.objects.create(
            value="Value 1", slug="value-1"
        )
        self.attribute_value2 = AttributeValue.objects.create(
            value="Value 2", slug="value-2"
        )

    def test_set_listing_attribute_values_success(self) -> None:
        """Тест успешного обновления значений атрибута листинга"""
        value_ids = [self.attribute_value1.id, self.attribute_value2.id]
        updated_listing_attribute = set_listing_attribute_values(
            listing_attribute_id=self.listing_attribute.id, value_ids=value_ids
        )
        self.assertIsNotNone(updated_listing_attribute)
        self.assertEqual(
            list(updated_listing_attribute._possible_values.all()),
            [self.attribute_value1, self.attribute_value2],
        )

    def test_set_listing_attribute_values_with_non_existent_value(
        self,
    ) -> None:
        """Тест обновления значений атрибута листинга с несуществующим значением"""
        non_existent_value_id = 9999
        value_ids = [self.attribute_value1.id, non_existent_value_id]

        with self.assertRaises(ObjectDoesNotExistException):
            set_listing_attribute_values(
                listing_attribute_id=self.listing_attribute.id,
                value_ids=value_ids,
            )
