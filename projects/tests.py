import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User

from .admin import AdminProjectForm
from .forms import ProjectForm
from .models import Project


class TemporaryMediaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_root = tempfile.mkdtemp()
        cls.media_override = override_settings(
            MEDIA_ROOT=cls.media_root,
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        )
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)


class ProjectTests(TemporaryMediaTestCase):
    def setUp(self):
        self.owner = self.create_user("owner@example.com", "+79990000001")
        self.member = self.create_user("member@example.com", "+79990000002")
        self.project = Project.objects.create(
            name="First project",
            description="Description",
            owner=self.owner,
            github_url="https://github.com/example/project",
            status="open",
        )
        self.project.participants.add(self.owner)

    @staticmethod
    def create_user(email, phone):
        return User.objects.create_user(
            email=email,
            password="Test-password-123",
            name=email.split("@", maxsplit=1)[0],
            surname="Test",
            phone=phone,
        )

    def test_project_forms_validate_status_and_github(self):
        form = ProjectForm()
        invalid_data = {
            "name": "Project",
            "description": "Description",
            "github_url": "https://github.com.example.org/project",
            "status": "open",
        }
        regular_form = ProjectForm(data=invalid_data)
        admin_form = AdminProjectForm(data=invalid_data)

        self.assertEqual(
            list(form.fields["status"].choices),
            [("open", "Открыт"), ("closed", "Закрыт")],
        )
        self.assertIn("github_url", regular_form.errors)
        self.assertIn("github_url", admin_form.errors)

    def test_public_list_is_paginated_newest_first_and_hides_create_button(self):
        for number in range(12):
            Project.objects.create(
                name=f"Project {number}", owner=self.owner, status="open"
            )

        response = self.client.get(reverse("projects:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 12)
        self.assertEqual(response.context["page_obj"][0].name, "Project 11")
        self.assertNotContains(response, "+ Создать проект")

    def test_authenticated_user_creates_project_and_becomes_participant(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "New project",
                "description": "Description",
                "github_url": "https://github.com/example/new-project",
                "status": "open",
            },
        )

        project = Project.objects.get(name="New project")
        self.assertRedirects(
            response,
            reverse("projects:detail", kwargs={"project_id": project.id}),
        )
        self.assertEqual(project.owner, self.member)
        self.assertTrue(project.participants.filter(pk=self.member.pk).exists())

    def test_only_owner_can_edit_project(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("projects:edit", kwargs={"project_id": self.project.id}),
            {
                "name": "Changed",
                "description": self.project.description,
                "github_url": self.project.github_url,
                "status": self.project.status,
            },
        )

        self.project.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.project.name, "First project")

    def test_only_owner_can_complete_project(self):
        url = reverse("projects:complete", kwargs={"project_id": self.project.id})
        self.client.force_login(self.member)
        forbidden_response = self.client.post(url)
        self.client.force_login(self.owner)
        owner_response = self.client.post(url)

        self.project.refresh_from_db()
        self.assertEqual(forbidden_response.status_code, 403)
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(self.project.status, "closed")

    def test_user_can_join_and_leave_but_owner_cannot_leave(self):
        url = reverse(
            "projects:toggle_participate",
            kwargs={"project_id": self.project.id},
        )
        self.client.force_login(self.member)
        join_response = self.client.post(url)
        leave_response = self.client.post(url)
        self.client.force_login(self.owner)
        owner_response = self.client.post(url)

        self.assertTrue(join_response.json()["participant"])
        self.assertFalse(leave_response.json()["participant"])
        self.assertEqual(owner_response.status_code, 403)
        self.assertTrue(self.project.participants.filter(pk=self.owner.pk).exists())

    def test_user_can_toggle_and_view_favorites(self):
        self.client.force_login(self.member)
        url = reverse(
            "projects:toggle_favorite",
            kwargs={"project_id": self.project.id},
        )
        add_response = self.client.post(url)
        favorites_response = self.client.get(reverse("projects:favorites"))
        remove_response = self.client.post(url)

        self.assertTrue(add_response.json()["favorited"])
        self.assertContains(favorites_response, self.project.name)
        self.assertFalse(remove_response.json()["favorited"])
