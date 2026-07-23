from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "description", "owner__email")
    list_select_related = ("owner",)
    autocomplete_fields = ("owner",)
    filter_horizontal = ("participants",)
    readonly_fields = ("created_at",)
    fields = (
        "name",
        "description",
        "owner",
        "github_url",
        "status",
        "participants",
        "created_at",
    )
