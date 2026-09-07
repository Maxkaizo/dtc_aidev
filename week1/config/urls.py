from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from chores import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.board, name="board"),
    path("chores/new/", views.create_chore, name="create_chore"),
    path("chores/<int:pk>/<str:action>/", views.chore_action, name="chore_action"),
]
