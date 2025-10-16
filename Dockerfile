# Используем официальный образ Python
FROM python:3.12

# Устанавливаем переменную окружения для предотвращения создания .pyc файлов
ENV PYTHONDONTWRITEBYTECODE 1
# Устанавливаем переменную окружения для буферизации вывода (для логов)
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию
WORKDIR /app

COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в рабочую директорию
COPY . .

# Открываем порт 8000 для сервера Django
EXPOSE 8000

# Команда для запуска сервера Django
CMD python manage.py runserver 0.0.0.0:8000
