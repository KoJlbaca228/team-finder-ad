from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project
from users.models import User

DEMO_PASSWORD = "TeamFinderDemo2026!"

DEMO_USERS = (
    {
        "email": "anna.ivanova@example.com",
        "name": "Анна",
        "surname": "Иванова",
        "phone": "+79990000001",
        "github_url": "https://github.com/team-finder-demo-anna",
        "about": "Разрабатываю полезные сервисы для городских сообществ.",
    },
    {
        "email": "boris.petrov@example.com",
        "name": "Борис",
        "surname": "Петров",
        "phone": "+79990000002",
        "github_url": "https://github.com/team-finder-demo-boris",
        "about": "Интересуюсь образовательными продуктами и аналитикой.",
    },
    {
        "email": "elena.smirnova@example.com",
        "name": "Елена",
        "surname": "Смирнова",
        "phone": "+79990000003",
        "github_url": "https://github.com/team-finder-demo-elena",
        "about": "Создаю проекты для общения и обмена знаниями.",
    },
)

DEMO_PROJECTS = (
    {
        "owner_email": "anna.ivanova@example.com",
        "name": "Сервис для волонтёров",
        "description": "Площадка для поиска городских волонтёрских инициатив.",
        "github_url": "https://github.com/team-finder-demo/volunteers",
        "status": "open",
    },
    {
        "owner_email": "boris.petrov@example.com",
        "name": "Учебный трекер",
        "description": "Приложение для планирования самостоятельного обучения.",
        "github_url": "https://github.com/team-finder-demo/study-tracker",
        "status": "open",
    },
    {
        "owner_email": "elena.smirnova@example.com",
        "name": "Книжный клуб",
        "description": "Сервис совместного чтения и обсуждения книг.",
        "github_url": "https://github.com/team-finder-demo/book-club",
        "status": "closed",
    },
)


class Command(BaseCommand):
    help = "Создаёт идемпотентный набор демонстрационных данных для варианта 1."

    def handle(self, *args, **options):
        with transaction.atomic():
            users, created_users = self._create_users()
            projects, created_projects = self._create_projects(users)
            self._create_relations(users, projects)

        self.stdout.write(
            self.style.SUCCESS(
                "Демонстрационные данные готовы: "
                f"пользователей создано {created_users}, "
                f"проектов создано {created_projects}."
            )
        )
        self.stdout.write(
            f"Пароль новых демонстрационных пользователей: {DEMO_PASSWORD}"
        )

    def _create_users(self):
        users = {}
        created_count = 0

        for user_data in DEMO_USERS:
            email = user_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    password=DEMO_PASSWORD,
                    **user_data,
                )
                created_count += 1
            users[email] = user

        return users, created_count

    def _create_projects(self, users):
        projects = {}
        created_count = 0

        for project_data in DEMO_PROJECTS:
            owner = users[project_data["owner_email"]]
            project, created = Project.objects.get_or_create(
                owner=owner,
                name=project_data["name"],
                defaults={
                    "description": project_data["description"],
                    "github_url": project_data["github_url"],
                    "status": project_data["status"],
                },
            )
            project.participants.add(owner)
            projects[project_data["owner_email"]] = project
            created_count += int(created)

        return projects, created_count

    @staticmethod
    def _create_relations(users, projects):
        anna = users["anna.ivanova@example.com"]
        boris = users["boris.petrov@example.com"]
        elena = users["elena.smirnova@example.com"]

        anna_project = projects[anna.email]
        boris_project = projects[boris.email]
        elena_project = projects[elena.email]

        anna_project.participants.add(boris)
        boris_project.participants.add(elena)
        elena_project.participants.add(anna)

        anna.favorites.add(boris_project)
        boris.favorites.add(elena_project)
        elena.favorites.add(anna_project)
