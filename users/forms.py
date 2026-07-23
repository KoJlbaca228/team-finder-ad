import re
from urllib.parse import urlparse

from django import forms
from django.db.models import Q

from .models import User


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
        }


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "Ссылка на GitHub",
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not re.fullmatch(r"(?:8|\+7)\d{10}", phone):
            raise forms.ValidationError("Введите номер в формате 8XXXXXXXXXX или +7XXXXXXXXXX")

        subscriber_number = phone[-10:]
        phone = f"+7{subscriber_number}"
        users = User.objects.filter(
            Q(phone=phone) | Q(phone=f"8{subscriber_number}")
        )
        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise forms.ValidationError("Этот номер телефона уже используется")
        return phone

    def clean_github_url(self):
        github_url = self.cleaned_data.get("github_url")
        if github_url and urlparse(github_url).hostname not in {"github.com", "www.github.com"}:
            raise forms.ValidationError("Ссылка должна вести на GitHub")
        return github_url
