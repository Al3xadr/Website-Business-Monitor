# WBM — Website Business Monitor

CLI-утилита для проверки доступности сайтов. Делает HTTP-запрос, измеряет время ответа и сообщает статус.

## Что делает

- Проверяет доступность сайта по URL
- Измеряет время ответа в секундах
- Определяет статус: UP (2xx, 3xx) или DOWN (4xx, 5xx, timeout, ошибка соединения)
- Корректно обрабатывает таймауты и ошибки подключения
- Возвращает структурированный результат — готовый к отправке в Telegram, БД или API

## Требования

- Python 3.9+
- pip

## Установка

```bash
git clone https://github.com/<your-username>/WBM.git
cd WBM

python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

## Запуск

```bash
python app/main.py <URL>
```

Пример:

```bash
python app/main.py https://example.com
```

Вывод:

```
======================
     Website Business Monitor
======================

URL: https://example.com

HTTP status: 200
Response time: 0.25 seconds
Reason: Site is reachable

Status: UP
```

Если URL не передан:

```bash
python app/main.py
```

```
Usage: python app/main.py <URL>
```

## Примеры

Проверить рабочий сайт:

```bash
python app/main.py https://example.com
```

Проверить несуществующий домен:

```bash
python app/main.py https://this-does-not-exist-12345.com
```

```
URL: https://this-does-not-exist-12345.com

Reason: Could not connect to site

Status: DOWN
```
