from django import forms

from users.forms import validate_github_url

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
        return validate_github_url(self.cleaned_data.get("github_url"))
