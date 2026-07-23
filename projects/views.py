from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project


def project_list(request):
    projects = Project.objects.all().order_by("-created_at")
    page_obj = Paginator(projects, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "projects/project_list.html",
        {"projects": projects, "page_obj": page_obj, "query_prefix": ""},
    )


def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, "projects/project-details.html", {"project": project})


@login_required(login_url="users:login")
def favorite_projects(request):
    projects = request.user.favorites.all().order_by("-created_at")
    return render(request, "projects/favorite_projects.html", {"projects": projects})


@login_required(login_url="users:login")
def create_project(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", project_id=project.id)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required(login_url="users:login")
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("projects:detail", project_id=project.id)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


@require_POST
@login_required(login_url="users:login")
def complete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user or project.status != "open":
        return JsonResponse({"status": "error"}, status=403)

    project.status = "closed"
    project.save(update_fields=("status",))
    return JsonResponse({"status": "ok", "project_status": "closed"})


@require_POST
@login_required(login_url="users:login")
def toggle_participate(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner == request.user:
        return JsonResponse({"status": "error"}, status=403)

    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


@require_POST
@login_required(login_url="users:login")
def toggle_favorite(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user.favorites.filter(pk=project.pk).exists():
        request.user.favorites.remove(project)
        favorited = False
    else:
        request.user.favorites.add(project)
        favorited = True
    return JsonResponse({"status": "ok", "favorited": favorited})
