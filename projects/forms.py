from urllib.parse import urlparse

from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    status = forms.ChoiceField(
        label="Статус",
        choices=(("open", "Открыт"), ("closed", "Закрыт")),
    )

    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название",
            "description": "Описание",
            "github_url": "Ссылка на GitHub",
        }

    def clean_github_url(self):
        github_url = self.cleaned_data.get("github_url")
        if github_url and urlparse(github_url).hostname not in {"github.com", "www.github.com"}:
            raise forms.ValidationError("Ссылка должна вести на GitHub")
        return github_url
