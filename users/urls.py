from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("list/", views.user_list, name="list"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("<int:user_id>/", views.user_detail, name="detail"),
]
