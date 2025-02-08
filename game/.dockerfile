# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости (если есть requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt || true

COPY . /app

# Запуск игрового приложения
CMD ["python", "game.py"]