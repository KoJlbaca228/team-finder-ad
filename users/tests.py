import shutil
import tempfile
from io import StringIO
from pathlib import Path

from PIL import Image
from django.contrib.auth import SESSION_KEY
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project

from .admin import AdminUserCreationForm
from .forms import ProfileForm
from .models import User


class TemporaryMediaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_root = tempfile.mkdtemp()
        cls.settings_override = override_settings(
            MEDIA_ROOT=cls.media_root,
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        )
        cls.settings_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.settings_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)

    @staticmethod
    def create_user(number=1, password="Test-password-123", **extra_fields):
        data = {
            "email": f"user{number}@example.com",
            "password": password,
            "name": f"User{number}",
            "surname": "Test",
            "phone": f"+7999000{number:04d}",
        }
        data.update(extra_fields)
        return User.objects.create_user(**data)


class UserModelAndFormTests(TemporaryMediaTestCase):
    def test_manager_hashes_password_and_generates_avatar(self):
        user = self.create_user(
            email="person@EXAMPLE.COM",
            password="Raw-password-123",
            name="Anna",
        )

        self.assertEqual(user.email, "person@example.com")
        self.assertTrue(user.check_password("Raw-password-123"))
        self.assertTrue(Path(user.avatar.path).is_file())
        with Image.open(user.avatar.path) as avatar:
            self.assertEqual(avatar.size, (256, 256))

    def test_manager_creates_superuser_with_required_flags(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="Admin-password-123",
            name="Admin",
            surname="Test",
            phone="+79990009999",
        )

        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_profile_form_normalizes_and_validates_contacts(self):
        user = self.create_user(number=1)
        self.create_user(number=2, phone="+79991112233")
        base_data = {
            "name": user.name,
            "surname": user.surname,
            "about": "About",
            "github_url": "https://github.com/example",
        }

        valid_form = ProfileForm(
            data={**base_data, "phone": "89992223344"},
            instance=user,
        )
        duplicate_form = ProfileForm(
            data={**base_data, "phone": "89991112233"},
            instance=user,
        )
        github_form = ProfileForm(
            data={
                **base_data,
                "phone": "+79993334455",
                "github_url": "https://github.com.example.org/profile",
            },
            instance=user,
        )

        self.assertTrue(valid_form.is_valid(), valid_form.errors)
        self.assertEqual(valid_form.cleaned_data["phone"], "+79992223344")
        self.assertIn("phone", duplicate_form.errors)
        self.assertIn("github_url", github_form.errors)


class UserViewTests(TemporaryMediaTestCase):
    def setUp(self):
        self.password = "Test-password-123"
        self.user = self.create_user(password=self.password)

    def test_registration_creates_anonymous_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "New",
                "surname": "User",
                "email": "new@example.com",
                "password": "New-password-123",
            },
        )

        user = User.objects.get(email="new@example.com")
        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(user.check_password("New-password-123"))
        self.assertTrue(user.avatar)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_can_login_and_logout(self):
        login_response = self.client.post(
            reverse("users:login"),
            {"email": self.user.email, "password": self.password},
        )
        logout_response = self.client.get(reverse("users:logout"))

        self.assertRedirects(login_response, reverse("projects:list"))
        self.assertRedirects(logout_response, reverse("projects:list"))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_can_edit_profile_and_change_password(self):
        self.client.force_login(self.user)
        profile_response = self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Updated",
                "surname": "User",
                "about": "Updated profile",
                "phone": "89991112233",
                "github_url": "https://github.com/updated",
            },
        )
        password_response = self.client.post(
            reverse("users:change_password"),
            {
                "old_password": self.password,
                "new_password1": "Changed-password-456",
                "new_password2": "Changed-password-456",
            },
        )

        self.user.refresh_from_db()
        self.assertEqual(profile_response.status_code, 302)
        self.assertEqual(password_response.status_code, 302)
        self.assertEqual(self.user.phone, "+79991112233")
        self.assertTrue(self.user.check_password("Changed-password-456"))
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)

    def test_guest_can_view_public_pages_but_not_edit_profile(self):
        list_response = self.client.get(reverse("users:list"))
        detail_response = self.client.get(
            reverse("users:detail", kwargs={"user_id": self.user.pk})
        )
        edit_response = self.client.get(reverse("users:edit_profile"))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertRedirects(
            edit_response,
            f"{reverse('users:login')}?next={reverse('users:edit_profile')}",
        )


class UserListAndVariantTests(TemporaryMediaTestCase):
    def test_user_list_is_paginated_by_twelve_newest_users(self):
        users = [self.create_user(number=number) for number in range(1, 14)]

        first_page = self.client.get(reverse("users:list"))
        second_page = self.client.get(reverse("users:list"), {"page": 2})

        self.assertEqual(list(first_page.context["page_obj"]), list(reversed(users[1:])))
        self.assertEqual(list(second_page.context["page_obj"]), [users[0]])

    def test_all_variant_one_user_filters(self):
        viewer = self.create_user(number=1)
        favorite_owner = self.create_user(number=2)
        joined_owner = self.create_user(number=3)
        admirer = self.create_user(number=4)
        participant = self.create_user(number=5)

        viewer_project = Project.objects.create(
            name="Viewer project", owner=viewer, status="open"
        )
        favorite_project = Project.objects.create(
            name="Favorite project", owner=favorite_owner, status="open"
        )
        joined_project = Project.objects.create(
            name="Joined project", owner=joined_owner, status="open"
        )
        viewer_project.participants.add(viewer, participant)
        favorite_project.participants.add(favorite_owner)
        joined_project.participants.add(joined_owner, viewer)
        viewer.favorites.add(favorite_project)
        admirer.favorites.add(viewer_project)
        self.client.force_login(viewer)

        expected = {
            "owners-of-favorite-projects": [favorite_owner],
            "owners-of-participating-projects": [joined_owner, viewer],
            "interested-in-my-projects": [admirer],
            "participants-of-my-projects": [participant, viewer],
        }
        for filter_name, expected_users in expected.items():
            with self.subTest(filter_name=filter_name):
                response = self.client.get(
                    reverse("users:list"), {"filter": filter_name}
                )
                self.assertEqual(list(response.context["page_obj"]), expected_users)


class AdminAndSeedTests(TemporaryMediaTestCase):
    def test_admin_creation_hashes_password_and_validates_contacts(self):
        valid_form = AdminUserCreationForm(
            data={
                "email": "admin-created@example.com",
                "name": "Admin",
                "surname": "Created",
                "phone": "+79990001234",
                "github_url": "https://github.com/admin-created",
                "about": "",
                "password1": "Admin-password-123",
                "password2": "Admin-password-123",
            }
        )
        self.assertTrue(valid_form.is_valid(), valid_form.errors)
        user = valid_form.save()

        invalid_form = AdminUserCreationForm(
            data={
                "email": "invalid@example.com",
                "name": "Invalid",
                "surname": "User",
                "phone": f"8{user.phone[-10:]}",
                "github_url": "https://github.com.example.org/profile",
                "about": "",
                "password1": "Admin-password-123",
                "password2": "Admin-password-123",
            }
        )

        self.assertTrue(user.check_password("Admin-password-123"))
        self.assertTrue(user.avatar)
        self.assertIn("phone", invalid_form.errors)
        self.assertIn("github_url", invalid_form.errors)

    def test_seed_command_is_idempotent(self):
        call_command("seed_demo_data", stdout=StringIO())
        first_counts = (User.objects.count(), Project.objects.count())
        call_command("seed_demo_data", stdout=StringIO())

        self.assertEqual(first_counts, (3, 3))
        self.assertEqual((User.objects.count(), Project.objects.count()), first_counts)
        self.assertFalse(User.objects.filter(owned_projects__isnull=True).exists())
