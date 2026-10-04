# Базовый образ — Python 3.12, slim-вариант (лёгкий)
FROM python:3.12-slim

# Переменные окружения:
# - PYTHONUNBUFFERED — логи сразу идут в stdout, а не копятся в буфере
# - PYTHONDONTWRITEBYTECODE — не создавать .pyc-файлы (они не нужны в контейнере)
# - PYTHONPATH — чтобы `python -m app.main` находил модули
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Рабочая папка внутри контейнера
WORKDIR /app

# Сначала копируем ТОЛЬКО requirements.txt
# Это позволяет Docker кешировать слой с зависимостями:
# если код меняется, а requirements.txt — нет, pip install не перезапустится
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Теперь копируем код приложения
COPY app/ ./app/

# Создаём папку для логов (даже если её нет)
RUN mkdir -p logs

# Запускаем WBM в режиме мониторинга
# -u — unbuffered (чтобы логи шли сразу)
CMD ["python", "-u", "-m", "app.main", "https://example.com"]