from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm

from .forms import normalize_phone, validate_github_url
from .models import User


class AdminUserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = (
            "email",
            "name",
            "surname",
            "phone",
            "github_url",
            "about",
        )

    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"])

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url"))


class AdminUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"], self.instance)

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url"))


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm

    list_display = (
        "email",
        "name",
        "surname",
        "phone",
        "is_active",
        "is_staff",
    )
    list_editable = ("is_active",)
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("email", "name", "surname", "phone")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Профиль",
            {
                "fields": (
                    "name",
                    "surname",
                    "avatar",
                    "about",
                    "phone",
                    "github_url",
                )
            },
        ),
        ("Избранное", {"fields": ("favorites",)}),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Вход в систему", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "phone",
                    "github_url",
                    "about",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    readonly_fields = ("last_login",)
    filter_horizontal = ("favorites", "groups", "user_permissions")
