import os
import shutil
import uuid
from io import BytesIO
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image as PilImage

from .services import create_image


class CreateImageTests(TestCase):

    media_root: str

    @classmethod
    def setUpTestData(cls) -> None:
        """Создаем директорию media/images/tests для сохранения изображений"""
        cls.media_root = "media/images/tests"
        os.makedirs(cls.media_root, exist_ok=True)

    def setUp(self) -> None:
        """Настройка тестовых данных"""
        self.image_name = "test_image"
        self.object_type = "tests"
        self.alt_text = "Test Image"
        self.image_file = self._create_test_image()

    def _create_test_image(self) -> SimpleUploadedFile:
        """Создаем тестовое изображение"""
        img = PilImage.new("RGB", (100, 100), color=(73, 109, 137))
        img_io = BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)
        return SimpleUploadedFile(
            "tests/test.jpg", img_io.read(), content_type="image/jpeg"
        )

    @patch("uuid.uuid4")
    @patch("django.utils.timezone.now")
    def test_create_image_success(
        self, mock_now: Mock, mock_uuid: Mock
    ) -> None:
        """Тест успешного создания изображения"""
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_now.return_value = timezone.datetime(2024, 6, 10)
        image_instance = create_image(
            name=self.image_name,
            object_type=self.object_type,
            image_file=self.image_file,
            alt_text=self.alt_text,
        )
        self.assertIsNotNone(image_instance)
        self.assertEqual(image_instance.alt, self.alt_text)
        self.assertTrue(
            image_instance.image.name.startswith(
                f"images/{self.object_type}/2024/6/{self.image_name}_12345678123456781234567812345678"
            )
        )

    def test_create_image_with_resize(self) -> None:
        """Тест создания изображения с изменением размера"""
        max_width = 50
        max_height = 50
        image_instance = create_image(
            name=self.image_name,
            object_type=self.object_type,
            image_file=self.image_file,
            alt_text=self.alt_text,
            max_width=max_width,
            max_height=max_height,
        )
        self.assertIsNotNone(image_instance)
        img = PilImage.open(image_instance.image)
        self.assertTrue(img.width <= max_width)
        self.assertTrue(img.height <= max_height)

    def test_image_file_deleted_on_instance_deletion(self) -> None:
        """Тест удаления файла изображения после удаления объекта"""
        test_image_instance = create_image(
            name="delete_test",
            object_type=self.object_type,
            image_file=self.image_file,
            alt_text=self.alt_text,
        )
        image_path = test_image_instance.image.path
        # Убедитесь, что файл существует
        self.assertTrue(os.path.isfile(image_path))

        # Удаляем объект
        test_image_instance.delete()

        # Проверяем, что файл был удален
        self.assertFalse(os.path.isfile(image_path))

    @classmethod
    def tearDownClass(cls) -> None:
        """Удаляем директорию media/images/tests после завершения тестов"""
        super().tearDownClass()
        shutil.rmtree(cls.media_root, ignore_errors=True)
