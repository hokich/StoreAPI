import os
import uuid
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from utils.exceptions import (
    ObjectAlreadyExistsException,
    ObjectDoesNotExistException,
    ParentCatalogIsNotCategoryException,
    ParentCatalogIsNotListingException,
)
from utils.for_tests import create_test_image

from ..models import Brand, Category, Collection, FreeTag, Listing, Selection
from ..services.catalog import (
    UpdateBrandDict,
    UpdateCategoryDict,
    UpdateCollectionDict,
    UpdateFreeTagDict,
    UpdateListingDict,
    UpdateSelectionDict,
    _check_catalog_exists_by_slug_and_parent,
    _get_slug_by_name,
    create_brand,
    create_category,
    create_collection,
    create_free_tag,
    create_listing,
    create_selection,
    set_brand_image,
    set_category_background_image,
    set_category_image,
    set_listing_background_image,
    set_listing_image,
    update_brand,
    update_category,
    update_collection,
    update_free_tag,
    update_listing,
    update_selection,
)


class CatalogUtilsTests(TestCase):

    def setUp(self) -> None:
        self.parent_catalog = Category.objects.create(
            name="Parent Catalog",
            slug="parent-catalog",
        )
        self.catalog = Category.objects.create(
            name="Test Catalog",
            slug="test-catalog",
            parent=self.parent_catalog,
        )

    def test_get_slug_by_name_unique(self) -> None:
        """Тест для генерации уникального slug"""
        slug = _get_slug_by_name("New Catalog")
        self.assertEqual(slug, "new-catalog")

    def test_get_slug_by_name_non_unique(self) -> None:
        """Тест для генерации уникального slug, если такой уже существует"""
        slug = _get_slug_by_name("Test Catalog", self.parent_catalog.id)
        self.assertEqual(slug, "test-catalog-1")

    def test_check_catalog_exists_by_slug_and_parent(self) -> None:
        """Тест проверки существования каталога по slug и parent_id"""
        exists = _check_catalog_exists_by_slug_and_parent(
            "test-catalog", self.parent_catalog.id
        )
        self.assertTrue(exists)

    def test_check_catalog_not_exists_by_slug_and_parent(self) -> None:
        """Тест проверки несуществования каталога по slug и parent_id"""
        exists = _check_catalog_exists_by_slug_and_parent(
            "non-existent-slug", self.parent_catalog.id
        )
        self.assertFalse(exists)


class CatalogProxyModelsTests(TestCase):

    def setUp(self) -> None:
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )

        self.brand = Brand.objects.create(
            name="Test Brand",
            slug="test-brand",
        )

    def test_get_object_by_slug_category(self) -> None:
        """Тест для метода get_object_by_slug для модели Category"""
        category = Category.get_object_by_slug("test-category")
        self.assertEqual(category, self.category)

    def test_get_object_by_slug_brand(self) -> None:
        """Тест для метода get_object_by_slug для модели Brand"""
        brand = Brand.get_object_by_slug("test-brand")
        self.assertEqual(brand, self.brand)

    def test_get_object_by_slug_does_not_exist(self) -> None:
        """Тест для метода get_object_by_slug при несуществующем объекте"""
        with self.assertRaises(ObjectDoesNotExistException):
            Category.get_object_by_slug("non-existent-slug")


class CreateCategoryTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для родительской категории
        self.parent_category = Category.objects.create(
            name="Parent Category",
            slug="parent-category",
        )

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_create_category_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного создания категории"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        category = create_category(
            name="New Category",
            parent_id=self.parent_category.id,
        )
        self.assertIsNotNone(category)
        self.assertEqual(category.name, "New Category")
        self.assertEqual(category.parent, self.parent_category)
        self.assertTrue(category.slug.startswith("new-category"))

    def test_create_category_with_existing_slug(self) -> None:
        """Тест создания категории с существующим slug"""
        Category.objects.create(
            name="Existing Category",
            slug="existing-category",
            parent=self.parent_category,
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_category(
                name="Existing Category",
                parent_id=self.parent_category.id,
                slug="existing-category",
            )

    def test_create_category_with_invalid_parent(self) -> None:
        """Тест создания категории с неверным родителем"""
        invalid_parent = Brand.objects.create(
            name="Invalid Parent",
            slug="invalid-parent",
        )

        with self.assertRaises(ParentCatalogIsNotCategoryException):
            create_category(
                name="Invalid Category",
                parent_id=invalid_parent.id,
            )

    def test_create_category_with_no_parent(self) -> None:
        """Тест создания категории без родительской категории"""
        with self.assertRaises(ObjectDoesNotExistException):
            create_category(
                name="Orphan Category",
                parent_id=999,  # Не существующий ID родителя
            )


class UpdateCategoryTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для родительской категории и категории
        self.parent_category = Category.objects.create(
            name="Parent Category", slug="parent-category"
        )
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            parent=self.parent_category,
        )

    def test_update_category_success(self) -> None:
        """Тест успешного обновления категории"""
        updated_data: UpdateCategoryDict = {
            "name": "Updated Category",
            "slug": None,
            "parent_id": self.parent_category.id,
            "short_name": "UpdCat",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        updated_category = update_category(
            category_id=self.category.id, category_data=updated_data
        )
        self.assertIsNotNone(updated_category)
        self.assertEqual(updated_category.name, "Updated Category")
        self.assertEqual(updated_category.slug, "updated-category")
        self.assertEqual(updated_category.short_name, "UpdCat")
        self.assertEqual(updated_category.color, "#ff5733")
        self.assertEqual(updated_category.icon, "updated-icon")

    def test_update_category_with_existing_slug(self) -> None:
        """Тест обновления категории с существующим slug"""
        Category.objects.create(
            name="Existing Category",
            slug="existing-category",
            parent=self.parent_category,
        )

        updated_data: UpdateCategoryDict = {
            "name": "Updated Category",
            "slug": "existing-category",
            "parent_id": self.parent_category.id,
            "short_name": "UpdCat",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        with self.assertRaises(ObjectAlreadyExistsException):
            update_category(
                category_id=self.category.id, category_data=updated_data
            )

    def test_update_category_with_invalid_parent(self) -> None:
        """Тест обновления категории с неверным родителем"""
        invalid_parent = Brand.objects.create(
            name="Invalid Parent", slug="invalid-parent"
        )

        updated_data: UpdateCategoryDict = {
            "name": "Updated Category",
            "slug": None,
            "parent_id": invalid_parent.id,
            "short_name": "UpdCat",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        with self.assertRaises(ParentCatalogIsNotCategoryException):
            update_category(
                category_id=self.category.id, category_data=updated_data
            )

    def test_update_category_with_no_parent(self) -> None:
        """Тест обновления категории без родительской категории"""
        updated_data: UpdateCategoryDict = {
            "name": "Updated Category",
            "slug": None,
            "parent_id": None,
            "short_name": "UpdCat",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        updated_category = update_category(
            category_id=self.category.id, category_data=updated_data
        )
        self.assertIsNotNone(updated_category)
        self.assertEqual(updated_category.parent, None)

    def test_update_category_with_non_existent_category(self) -> None:
        """Тест обновления несуществующей категории"""
        updated_data: UpdateCategoryDict = {
            "name": "Updated Category",
            "slug": None,
            "parent_id": self.parent_category.id,
            "short_name": "UpdCat",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        with self.assertRaises(ObjectDoesNotExistException):
            update_category(
                category_id=999,  # Не существующий ID категории
                category_data=updated_data,
            )


class SetCategoryBackgroundImageTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовую категорию
        self.category = Category.objects.create(
            name="Test Category", slug="test-category"
        )
        self.image_file = create_test_image()
        self.created_files: list[str] = []

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_set_category_background_image_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного обновления фонового изображения категории"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        updated_category = set_category_background_image(
            category_id=self.category.id, background_file=self.image_file
        )
        self.assertIsNotNone(updated_category.background)
        background_path = updated_category.background.image.path
        self.created_files.append(background_path)

        self.assertTrue(os.path.isfile(background_path))

    def test_remove_category_background_image(self) -> None:
        """Тест удаления фонового изображения категории"""
        # Устанавливаем фоновое изображение
        updated_category = set_category_background_image(
            category_id=self.category.id, background_file=self.image_file
        )
        background_path = updated_category.background.image.path
        self.created_files.append(background_path)

        # Удаляем фоновое изображение
        updated_category = set_category_background_image(
            category_id=self.category.id, background_file=None
        )
        self.assertIsNone(updated_category.background)
        self.assertFalse(os.path.isfile(background_path))

    def test_set_category_background_image_non_existent_category(self) -> None:
        """Тест установки фонового изображения для несуществующей категории"""
        with self.assertRaises(ObjectDoesNotExistException):
            set_category_background_image(
                category_id=999,  # Не существующий ID категории
                background_file=self.image_file,
            )

    def tearDown(self) -> None:
        """Удаляем файлы, созданные в рамках тестов"""
        for file_path in self.created_files:
            if os.path.isfile(file_path):
                os.remove(file_path)


class SetCategoryImageTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовую категорию
        self.category = Category.objects.create(
            name="Test Category", slug="test-category"
        )
        self.image_file = create_test_image()
        self.created_files: list[str] = []

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_set_category_image_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного обновления изображения категории"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        updated_category = set_category_image(
            category_id=self.category.id, image_file=self.image_file
        )
        self.assertIsNotNone(updated_category.image)
        image_path = updated_category.image.image.path
        self.created_files.append(image_path)

        self.assertTrue(os.path.isfile(image_path))

    def test_remove_category_image(self) -> None:
        """Тест удаления изображения категории"""
        # Устанавливаем изображение
        updated_category = set_category_image(
            category_id=self.category.id, image_file=self.image_file
        )
        image_path = updated_category.image.image.path
        self.created_files.append(image_path)

        # Удаляем изображение
        updated_category = set_category_image(
            category_id=self.category.id, image_file=None
        )
        self.assertIsNone(updated_category.image)
        self.assertFalse(os.path.isfile(image_path))

    def test_set_category_image_non_existent_category(self) -> None:
        """Тест установки изображения для несуществующей категории"""
        with self.assertRaises(ObjectDoesNotExistException):
            set_category_image(
                category_id=999,  # Не существующий ID категории
                image_file=self.image_file,
            )

    def tearDown(self) -> None:
        """Удаляем файлы, созданные в рамках тестов"""
        for file_path in self.created_files:
            if os.path.isfile(file_path):
                os.remove(file_path)


class CreateListingTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для родительской категории
        self.parent_category = Category.objects.create(
            name="Parent Category", slug="parent-category"
        )

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_create_listing_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного создания списка"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        listing = create_listing(
            name="New Listing",
            parent_id=self.parent_category.id,
        )
        self.assertIsNotNone(listing)
        self.assertEqual(listing.name, "New Listing")
        self.assertEqual(listing.parent, self.parent_category)
        self.assertTrue(listing.slug.startswith("new-listing"))

    def test_create_listing_with_existing_slug(self) -> None:
        """Тест создания списка с существующим slug"""
        Listing.objects.create(
            name="Existing Listing",
            slug="existing-listing",
            parent=self.parent_category,
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_listing(
                name="Existing Listing",
                parent_id=self.parent_category.id,
                slug="existing-listing",
            )

    def test_create_listing_with_invalid_parent(self) -> None:
        """Тест создания списка с неверным родителем"""
        invalid_parent = Brand.objects.create(
            name="Invalid Parent", slug="invalid-parent"
        )

        with self.assertRaises(ParentCatalogIsNotCategoryException):
            create_listing(
                name="Invalid Listing",
                parent_id=invalid_parent.id,
            )

    def test_create_listing_with_no_parent(self) -> None:
        """Тест создания списка без родительской категории"""
        with self.assertRaises(ObjectDoesNotExistException):
            create_listing(
                name="Orphan Listing",
                parent_id=999,  # Не существующий ID родителя
            )


class UpdateListingTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для родительской категории и листинга
        self.parent_category = Category.objects.create(
            name="Parent Category", slug="parent-category"
        )
        self.listing = Listing.objects.create(
            name="Test Listing",
            slug="test-listing",
            parent=self.parent_category,
        )

    def test_update_listing_success(self) -> None:
        """Тест успешного обновления листинга"""
        updated_data: UpdateListingDict = {
            "name": "Updated Listing",
            "slug": None,
            "parent_id": self.parent_category.id,
            "short_name": "UpdList",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        updated_listing = update_listing(
            listing_id=self.listing.id, listing_data=updated_data
        )
        self.assertIsNotNone(updated_listing)
        self.assertEqual(updated_listing.name, "Updated Listing")
        self.assertEqual(updated_listing.slug, "updated-listing")
        self.assertEqual(updated_listing.short_name, "UpdList")
        self.assertEqual(updated_listing.color, "#ff5733")
        self.assertEqual(updated_listing.icon, "updated-icon")

    def test_update_listing_with_existing_slug(self) -> None:
        """Тест обновления листинга с существующим slug"""
        Listing.objects.create(
            name="Existing Listing",
            slug="existing-listing",
            parent=self.parent_category,
        )

        updated_data: UpdateListingDict = {
            "name": "Updated Listing",
            "slug": "existing-listing",
            "parent_id": self.parent_category.id,
            "short_name": "UpdList",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        with self.assertRaises(ObjectAlreadyExistsException):
            update_listing(
                listing_id=self.listing.id, listing_data=updated_data
            )

    def test_update_listing_with_invalid_parent(self) -> None:
        """Тест обновления листинга с неверным родителем"""
        invalid_parent = Brand.objects.create(
            name="Invalid Parent", slug="invalid-parent"
        )

        updated_data: UpdateListingDict = {
            "name": "Updated Listing",
            "slug": None,
            "parent_id": invalid_parent.id,
            "short_name": "UpdList",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        with self.assertRaises(ParentCatalogIsNotCategoryException):
            update_listing(
                listing_id=self.listing.id, listing_data=updated_data
            )

    def test_update_listing_with_no_parent(self) -> None:
        """Тест обновления листинга без родительской категории"""
        updated_data: UpdateListingDict = {
            "name": "Updated Listing",
            "slug": None,
            "parent_id": None,
            "short_name": "UpdList",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        updated_listing = update_listing(
            listing_id=self.listing.id, listing_data=updated_data
        )
        self.assertIsNotNone(updated_listing)
        self.assertEqual(updated_listing.parent, None)

    def test_update_listing_with_non_existent_listing(self) -> None:
        """Тест обновления несуществующего листинга"""
        updated_data: UpdateListingDict = {
            "name": "Updated Listing",
            "slug": None,
            "parent_id": self.parent_category.id,
            "short_name": "UpdList",
            "color": "#ff5733",
            "icon": "updated-icon",
        }

        with self.assertRaises(ObjectDoesNotExistException):
            update_listing(
                listing_id=999,  # Не существующий ID листинга
                listing_data=updated_data,
            )


class SetListingImageTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовый листинг
        self.listing = Listing.objects.create(
            name="Test Listing", slug="test-listing"
        )
        self.image_file = create_test_image()
        self.created_files: list[str] = []

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_set_listing_image_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного обновления изображения листинга"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        updated_listing = set_listing_image(
            listing_id=self.listing.id, image_file=self.image_file
        )
        self.assertIsNotNone(updated_listing.image)
        image_path = updated_listing.image.image.path
        self.created_files.append(image_path)

        self.assertTrue(os.path.isfile(image_path))

    def test_remove_listing_image(self) -> None:
        """Тест удаления изображения листинга"""
        # Устанавливаем изображение
        updated_listing = set_listing_image(
            listing_id=self.listing.id, image_file=self.image_file
        )
        image_path = updated_listing.image.image.path
        self.created_files.append(image_path)

        # Удаляем изображение
        updated_listing = set_listing_image(
            listing_id=self.listing.id, image_file=None
        )
        self.assertIsNone(updated_listing.image)
        self.assertFalse(os.path.isfile(image_path))

    def test_set_listing_image_non_existent_listing(self) -> None:
        """Тест установки изображения для несуществующего листинга"""
        with self.assertRaises(ObjectDoesNotExistException):
            set_listing_image(
                listing_id=999,  # Не существующий ID листинга
                image_file=self.image_file,
            )

    def tearDown(self) -> None:
        """Удаляем файлы, созданные в рамках тестов"""
        for file_path in self.created_files:
            if os.path.isfile(file_path):
                os.remove(file_path)


class SetListingBackgroundImageTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовый листинг
        self.listing = Listing.objects.create(
            name="Test Listing", slug="test-listing"
        )
        self.image_file = create_test_image()
        self.created_files: list[str] = []

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_set_listing_bg_image_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного обновления изображения листинга"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        updated_listing = set_listing_background_image(
            listing_id=self.listing.id, image_file=self.image_file
        )
        self.assertIsNotNone(updated_listing.background)
        image_path = updated_listing.background.image.path
        self.created_files.append(image_path)

        self.assertTrue(os.path.isfile(image_path))

    def test_remove_listing_bg_image(self) -> None:
        """Тест удаления изображения листинга"""
        # Устанавливаем изображение
        updated_listing = set_listing_background_image(
            listing_id=self.listing.id, image_file=self.image_file
        )
        image_path = updated_listing.background.image.path
        self.created_files.append(image_path)

        # Удаляем изображение
        updated_listing = set_listing_background_image(
            listing_id=self.listing.id, image_file=None
        )
        self.assertIsNone(updated_listing.background)
        self.assertFalse(os.path.isfile(image_path))

    def test_set_listing_bg_image_non_existent_listing(self) -> None:
        """Тест установки изображения для несуществующего листинга"""
        with self.assertRaises(ObjectDoesNotExistException):
            set_listing_image(
                listing_id=999,  # Не существующий ID листинга
                image_file=self.image_file,
            )

    def tearDown(self) -> None:
        """Удаляем файлы, созданные в рамках тестов"""
        for file_path in self.created_files:
            if os.path.isfile(file_path):
                os.remove(file_path)


class CreateCollectionTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для родительского списка
        self.parent_listing = Listing.objects.create(
            name="Parent Listing", slug="parent-listing"
        )

    @patch("uuid.uuid4")
    def test_create_collection_success(self, mock_uuid: Mock) -> None:
        """Тест успешного создания коллекции"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")

        collection = create_collection(
            name="New Collection",
            parent_id=self.parent_listing.id,
            color="#ff5733",
            active_filters={"filter_key": "filter_value"},
        )
        self.assertIsNotNone(collection)
        self.assertEqual(collection.name, "New Collection")
        self.assertEqual(collection.parent, self.parent_listing)
        self.assertEqual(collection.color, "#ff5733")
        self.assertEqual(
            collection.active_filters, {"filter_key": "filter_value"}
        )
        self.assertTrue(collection.slug.startswith("new-collection"))

    def test_create_collection_with_existing_slug(self) -> None:
        """Тест создания коллекции с существующим slug"""
        Collection.objects.create(
            name="Existing Collection",
            slug="existing-collection",
            parent=self.parent_listing,
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_collection(
                name="Existing Collection",
                parent_id=self.parent_listing.id,
                slug="existing-collection",
            )

    def test_create_collection_with_invalid_parent(self) -> None:
        """Тест создания коллекции с неверным родителем"""
        invalid_parent = Category.objects.create(
            name="Invalid Parent", slug="invalid-parent"
        )

        with self.assertRaises(ParentCatalogIsNotListingException):
            create_collection(
                name="Invalid Collection", parent_id=invalid_parent.id
            )

    def test_create_collection_with_no_parent(self) -> None:
        """Тест создания коллекции без родительской категории"""
        with self.assertRaises(ObjectDoesNotExistException):
            create_collection(
                name="Orphan Collection",
                parent_id=999,  # Не существующий ID родителя
            )


class UpdateCollectionTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для родительского листинга и коллекции
        self.parent_listing = Listing.objects.create(
            name="Parent Listing", slug="parent-listing"
        )
        self.collection = Collection.objects.create(
            name="Test Collection",
            slug="test-collection",
            parent=self.parent_listing,
        )

    def test_update_collection_success(self) -> None:
        """Тест успешного обновления коллекции"""
        updated_data: UpdateCollectionDict = {
            "name": "Updated Collection",
            "slug": None,
            "parent_id": self.parent_listing.id,
            "short_name": "UpdColl",
            "color": "#ff5733",
            "active_filters": {"filter_key": "filter_value"},
        }

        updated_collection = update_collection(
            collection_id=self.collection.id, collection_data=updated_data
        )
        self.assertIsNotNone(updated_collection)
        self.assertEqual(updated_collection.name, "Updated Collection")
        self.assertEqual(updated_collection.slug, "updated-collection")
        self.assertEqual(updated_collection.short_name, "UpdColl")
        self.assertEqual(updated_collection.color, "#ff5733")
        self.assertEqual(
            updated_collection.active_filters, {"filter_key": "filter_value"}
        )

    def test_update_collection_with_existing_slug(self) -> None:
        """Тест обновления коллекции с существующим slug"""
        Collection.objects.create(
            name="Existing Collection",
            slug="existing-collection",
            parent=self.parent_listing,
        )

        updated_data: UpdateCollectionDict = {
            "name": "Updated Collection",
            "slug": "existing-collection",
            "parent_id": self.parent_listing.id,
            "short_name": "UpdColl",
            "color": "#ff5733",
            "active_filters": {"filter_key": "filter_value"},
        }

        with self.assertRaises(ObjectAlreadyExistsException):
            update_collection(
                collection_id=self.collection.id, collection_data=updated_data
            )

    def test_update_collection_with_invalid_parent(self) -> None:
        """Тест обновления коллекции с неверным родителем"""
        invalid_parent = Brand.objects.create(
            name="Invalid Parent", slug="invalid-parent"
        )

        updated_data: UpdateCollectionDict = {
            "name": "Updated Collection",
            "slug": None,
            "parent_id": invalid_parent.id,
            "short_name": "UpdColl",
            "color": "#ff5733",
            "active_filters": {"filter_key": "filter_value"},
        }

        with self.assertRaises(ParentCatalogIsNotListingException):
            update_collection(
                collection_id=self.collection.id, collection_data=updated_data
            )

    def test_update_collection_with_non_existent_collection(self) -> None:
        """Тест обновления несуществующей коллекции"""
        updated_data: UpdateCollectionDict = {
            "name": "Updated Collection",
            "slug": None,
            "parent_id": self.parent_listing.id,
            "short_name": "UpdColl",
            "color": "#ff5733",
            "active_filters": {"filter_key": "filter_value"},
        }

        with self.assertRaises(ObjectDoesNotExistException):
            update_collection(
                collection_id=999,  # Не существующий ID коллекции
                collection_data=updated_data,
            )


class CreateBrandTests(TestCase):

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_create_brand_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного создания бренда"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        brand = create_brand(name="New Brand", color="#ff5733")
        self.assertIsNotNone(brand)
        self.assertEqual(brand.name, "New Brand")
        self.assertEqual(brand.color, "#ff5733")
        self.assertTrue(brand.slug.startswith("new-brand"))

    def test_create_brand_with_existing_slug(self) -> None:
        """Тест создания бренда с существующим slug"""
        Brand.objects.create(name="Existing Brand", slug="existing-brand")

        with self.assertRaises(ObjectAlreadyExistsException):
            create_brand(
                name="Existing Brand",
                slug="existing-brand",
            )


class UpdateBrandTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для бренда
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")

    def test_update_brand_success(self) -> None:
        """Тест успешного обновления бренда"""
        updated_data: UpdateBrandDict = {
            "name": "Updated Brand",
            "slug": None,
            "short_name": "UpdBrand",
            "color": "#ff5733",
        }

        updated_brand = update_brand(
            brand_id=self.brand.id, brand_data=updated_data
        )
        self.assertIsNotNone(updated_brand)
        self.assertEqual(updated_brand.name, "Updated Brand")
        self.assertEqual(updated_brand.slug, "updated-brand")
        self.assertEqual(updated_brand.short_name, "UpdBrand")
        self.assertEqual(updated_brand.color, "#ff5733")

    def test_update_brand_with_non_existent_brand(self) -> None:
        """Тест обновления несуществующего бренда"""
        updated_data: UpdateBrandDict = {
            "name": "Updated Brand",
            "slug": None,
            "short_name": "UpdBrand",
            "color": "#ff5733",
        }

        with self.assertRaises(ObjectDoesNotExistException):
            update_brand(
                brand_id=999,  # Не существующий ID бренда
                brand_data=updated_data,
            )


class SetBrandImageTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовый бренд
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.image_file = create_test_image()
        self.created_files: list[str] = []

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_set_brand_image_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного обновления изображения бренда"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        updated_brand = set_brand_image(
            brand_id=self.brand.id, image_file=self.image_file
        )
        self.assertIsNotNone(updated_brand.image)
        image_path = updated_brand.image.image.path
        self.created_files.append(image_path)

        self.assertTrue(os.path.isfile(image_path))

    def test_remove_brand_image(self) -> None:
        """Тест удаления изображения бренда"""
        # Устанавливаем изображение
        updated_brand = set_brand_image(
            brand_id=self.brand.id, image_file=self.image_file
        )
        image_path = updated_brand.image.image.path
        self.created_files.append(image_path)

        # Удаляем изображение
        updated_brand = set_brand_image(
            brand_id=self.brand.id, image_file=None
        )
        self.assertIsNone(updated_brand.image)
        self.assertFalse(os.path.isfile(image_path))

    def test_set_brand_image_non_existent_brand(self) -> None:
        """Тест установки изображения для несуществующего бренда"""
        with self.assertRaises(ObjectDoesNotExistException):
            set_brand_image(
                brand_id=999,  # Не существующий ID бренда
                image_file=self.image_file,
            )

    def tearDown(self) -> None:
        """Удаляем файлы, созданные в рамках тестов"""
        for file_path in self.created_files:
            if os.path.isfile(file_path):
                os.remove(file_path)


class CreateSelectionTests(TestCase):

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_create_selection_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного создания подборки"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        selection = create_selection(name="New Selection", color="#ff5733")
        self.assertIsNotNone(selection)
        self.assertEqual(selection.name, "New Selection")
        self.assertEqual(selection.color, "#ff5733")
        self.assertTrue(selection.slug.startswith("new-selection"))

    def test_create_selection_with_existing_slug(self) -> None:
        """Тест создания подборки с существующим slug"""
        Selection.objects.create(
            name="Existing Selection", slug="existing-selection"
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_selection(
                name="Existing Selection", slug="existing-selection"
            )


class UpdateSelectionTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для подборки
        self.selection = Selection.objects.create(
            name="Test Selection", slug="test-selection"
        )

    def test_update_selection_success(self) -> None:
        """Тест успешного обновления подборки"""
        updated_data: UpdateSelectionDict = {
            "name": "Updated Selection",
            "slug": None,
            "short_name": "UpdSel",
            "color": "#ff5733",
        }

        updated_selection = update_selection(
            selection_id=self.selection.id, selection_data=updated_data
        )
        self.assertIsNotNone(updated_selection)
        self.assertEqual(updated_selection.name, "Updated Selection")
        self.assertEqual(updated_selection.slug, "updated-selection")
        self.assertEqual(updated_selection.short_name, "UpdSel")
        self.assertEqual(updated_selection.color, "#ff5733")

    def test_update_selection_with_existing_slug(self) -> None:
        """Тест обновления подборки с существующим slug"""
        Selection.objects.create(
            name="Existing Selection", slug="existing-selection"
        )

        updated_data: UpdateSelectionDict = {
            "name": "Updated Selection",
            "slug": "existing-selection",
            "short_name": "UpdSel",
            "color": "#ff5733",
        }

        with self.assertRaises(ObjectAlreadyExistsException):
            update_selection(
                selection_id=self.selection.id, selection_data=updated_data
            )

    def test_update_selection_with_non_existent_selection(self) -> None:
        """Тест обновления несуществующей подборки"""
        updated_data: UpdateSelectionDict = {
            "name": "Updated Selection",
            "slug": None,
            "short_name": "UpdSel",
            "color": "#ff5733",
        }

        with self.assertRaises(ObjectDoesNotExistException):
            update_selection(
                selection_id=999,  # Не существующий ID подборки
                selection_data=updated_data,
            )


class CreateFreeTagTests(TestCase):

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_create_free_tag_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного создания свободного тега"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.make_aware(
            timezone.datetime(2024, 6, 10)
        )

        free_tag = create_free_tag(name="New FreeTag", color="#ff5733")
        self.assertIsNotNone(free_tag)
        self.assertEqual(free_tag.name, "New FreeTag")
        self.assertEqual(free_tag.color, "#ff5733")
        self.assertTrue(free_tag.slug.startswith("new-freetag"))

    def test_create_free_tag_with_existing_slug(self) -> None:
        """Тест создания свободного тега с существующим slug"""
        FreeTag.objects.create(
            name="Existing FreeTag", slug="existing-freetag"
        )

        with self.assertRaises(ObjectAlreadyExistsException):
            create_free_tag(name="Existing FreeTag", slug="existing-freetag")


class UpdateFreeTagTests(TestCase):

    def setUp(self) -> None:
        # Создаем тестовые данные для свободного тега
        self.free_tag = FreeTag.objects.create(
            name="Test FreeTag", slug="test-freetag"
        )

    def test_update_free_tag_success(self) -> None:
        """Тест успешного обновления свободного тега"""
        updated_data: UpdateFreeTagDict = {
            "name": "Updated FreeTag",
            "slug": None,
            "short_name": "UpdTag",
            "color": "#ff5733",
        }

        updated_free_tag = update_free_tag(
            free_tag_id=self.free_tag.id, free_tag_data=updated_data
        )
        self.assertIsNotNone(updated_free_tag)
        self.assertEqual(updated_free_tag.name, "Updated FreeTag")
        self.assertEqual(updated_free_tag.slug, "updated-freetag")
        self.assertEqual(updated_free_tag.short_name, "UpdTag")
        self.assertEqual(updated_free_tag.color, "#ff5733")

    def test_update_free_tag_with_existing_slug(self) -> None:
        """Тест обновления свободного тега с существующим slug"""
        FreeTag.objects.create(
            name="Existing FreeTag", slug="existing-freetag"
        )

        updated_data: UpdateFreeTagDict = {
            "name": "Updated FreeTag",
            "slug": "existing-freetag",
            "short_name": "UpdTag",
            "color": "#ff5733",
        }

        with self.assertRaises(ObjectAlreadyExistsException):
            update_free_tag(
                free_tag_id=self.free_tag.id, free_tag_data=updated_data
            )

    def test_update_free_tag_with_non_existent_free_tag(self) -> None:
        """Тест обновления несуществующего свободного тега"""
        updated_data: UpdateFreeTagDict = {
            "name": "Updated FreeTag",
            "slug": None,
            "short_name": "UpdTag",
            "color": "#ff5733",
        }

        with self.assertRaises(ObjectDoesNotExistException):
            update_free_tag(
                free_tag_id=999,  # Не существующий ID свободного тега
                free_tag_data=updated_data,
            )
