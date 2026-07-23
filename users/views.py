from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import User


def user_list(request):
    participants = User.objects.all().order_by("-id")
    active_filter = request.GET.get("filter", "")

    if request.user.is_authenticated and active_filter:
        filters = {
            "owners-of-favorite-projects": {
                "id__in": request.user.favorites.values("owner_id")
            },
            "owners-of-participating-projects": {
                "id__in": request.user.participated_projects.values("owner_id")
            },
            "interested-in-my-projects": {"favorites__owner": request.user},
            "participants-of-my-projects": {
                "participated_projects__owner": request.user
            },
        }
        if active_filter in filters:
            participants = participants.filter(**filters[active_filter]).distinct()
        else:
            active_filter = ""
    else:
        active_filter = ""

    page_obj = Paginator(participants, 12).get_page(request.GET.get("page"))
    query_prefix = f"filter={active_filter}&" if active_filter else ""
    return render(
        request,
        "users/participants.html",
        {
            "participants": participants,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "query_prefix": query_prefix,
        },
    )


def user_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": user})


def register_user(request):
    if request.user.is_authenticated:
        return redirect("projects:list")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        User.objects.create_user(**form.cleaned_data)
        return redirect("users:login")
    return render(request, "users/register.html", {"form": form})


def login_user(request):
    if request.user.is_authenticated:
        return redirect("projects:list")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            return redirect("projects:list")
        form.add_error(None, "Неверный email или пароль")
    return render(request, "users/login.html", {"form": form})


@login_required(login_url="users:login")
def edit_profile(request):
    form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:detail", user_id=request.user.id)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required(login_url="users:login")
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", user_id=user.id)
    return render(request, "users/change_password.html", {"form": form})


def logout_user(request):
    logout(request)
    return redirect("projects:list")
