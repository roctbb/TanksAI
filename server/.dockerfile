# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости (если есть requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt || true

# Копируем файлы проекта в контейнер
COPY . /app

# Запуск серверного приложения
CMD ["python", "server.py"]