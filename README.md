# 🚀 Event Booking API

Учебный проект бэкенда для сервиса, где организаторы публикуют мероприятия (концерты, лекции, мастер-классы), а пользователи бронируют на них места. Система обрабатывает оплату, отправляет уведомления.

---

## 🚀 Возможности

- Просмотр списка мероприятий с фильтрацией и пагинацией.
- Получение детальной информации о мероприятии.
- Бронирование мест на выбранное событие.
- Отмена бронирования.
- Проверка доступности мест в реальном времени.
- Отправка уведомлений (email) о статусе бронирования через фоновые задачи.
- Защита от двойного бронирования (конкурентный доступ).

---

## 🛠 Стек технологий

- **Backend:** Python 3.11+, FastAPI
- **ORM:** SQLAlchemy (Async)
- **База данных:** PostgreSQL
- **Кэш и очереди:** Redis, Celery
- **Брокер задач:** RabbitMQ
- **Валидация данных:** Pydantic
- **Аутентификация:** JWT (Access + Refresh токены)
- **Тестирование:** pytest, httpx
- **Конфигурация:** pydantic-settings
- **Миграции:** Alembic

---

## ⚙️ Переменные окружения (.env)

Для конфигурации приложения создайте файл `.env` в корне проекта. Пример заполнения:

```env
SECRET_KEY = ire634*&6%^%451r2ewf1244g54345&@>??<fERGGJKfjij478fd4h56fj4j12fgh1b0v02g
DB_HOST = localhost #postgres - для запуска через docker-compose
DB_PORT = 5432
DB_USER = postgres
DB_PASS = password
DB_NAME = db_project
ACCESS_MAX_AGE = 900
REFRESH_MAX_AGE = 604800
EMAIL_HOST = smtp.yandex.ru
EMAIL_PORT = 465
EMAIL_USERNAME = user
EMAIL_PASSWORD = password
REDIS_HOST = 127.0.0.1 #redis - для запуска через docker-compose
REDIS_PORT = 6379
REDIS_DB = 0
FRONTEND_URL = http://127.0.0.1:8000/api/v1
RABBIT_HOST = 127.0.0.1 #rabbitmq - для запуска через docker-compose
RABBIT_USER = guest
RABBIT_PASS = guest
RABBIT_PORT = 5672
HMAC_KEY = jdie451f211c566s2s2d777fdqa
```

## 📦 Установка и запуск

### Требования

- Python 3.11 или выше
- Docker и Docker Compose (рекомендуется)

### Быстрый старт через Docker Compose

```bash
git clone https://github.com/max-dv800/fastapi-project.git
cd fastapi-project
docker-compose up --build



