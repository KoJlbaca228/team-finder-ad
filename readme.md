# TeamFinder

TeamFinder — Django-приложение для публикации проектов и поиска участников.
Реализован вариант №1: избранные проекты и фильтрация пользователей.

## Требования

- Python 3.13;
- Docker Desktop или Docker Engine с Compose;
- Git.

## Запуск проекта

Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
```

Активация в Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Активация в Linux или macOS:

```bash
source .venv/bin/activate
```

Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

Создайте `.env` из примера.

Windows PowerShell:

```powershell
Copy-Item .env_example .env
```

Linux или macOS:

```bash
cp .env_example .env
```

Сгенерировать секретный ключ можно командой:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Запишите результат в `DJANGO_SECRET_KEY` файла `.env`.

## Запуск в Docker

Соберите и запустите Django вместе с PostgreSQL:

```bash
docker compose up --build -d
```

Контейнер `web` дождётся готовности базы, применит миграции, соберёт статику и
запустит приложение по адресу <http://localhost:8000>.

Создайте администратора:

```bash
docker compose exec web python manage.py createsuperuser
```

Добавьте демонстрационные данные:

```bash
docker compose exec web python manage.py seed_demo_data
```

Посмотреть логи:

```bash
docker compose logs -f web
```

Команда идемпотентна: повторный запуск не создаёт дубликаты. Она создаёт трёх
пользователей, по одному проекту от каждого, участников и избранное. Пароль
демонстрационных пользователей выводится после выполнения команды.

Остановить контейнеры:

```bash
docker compose down
```

Данные PostgreSQL и загруженные изображения сохраняются в Docker volumes
`postgres_data` и `media_data`.

## Локальный запуск Django

Если Django должен работать из виртуального окружения, запустите только базу:

```bash
docker compose up -d db
```

Контейнер публикует PostgreSQL по адресу `localhost:5433`, потому что стандартный
порт `5432` может быть занят локальным сервером PostgreSQL.

Примените миграции и подготовьте данные:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
```

Запустите сервер:

```bash
python manage.py runserver
```

Приложение будет доступно по адресу <http://localhost:8000>, административная
панель — по адресу <http://localhost:8000/admin/>.

Остановить базу:

```bash
docker compose down
```

## Проверка

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Решения по противоречиям в документации

В итоговой реализации приоритет отдан функциональному описанию и финальному
чек-листу:

- после регистрации пользователь перенаправляется на страницу входа без
  автоматической авторизации;
- пользователи выводятся от новых к старым;
- email не редактируется в профиле, поскольку его нет в детальной спецификации
  формы и в готовом шаблоне;
- телефон заполняется при редактировании профиля, поскольку форма регистрации
  по чек-листу содержит только имя, фамилию, email и пароль.
