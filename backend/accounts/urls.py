from django.urls import path
from .views import (
    MeView,
    SignupView,
    VerifyEmailView,
    AdminUsersView,
    AdminDeleteUserView,
    AdminImportUsersCSVView,
)

urlpatterns = [
    # PUBLIC / USER
    path("me/", MeView.as_view()),
    path("signup/", SignupView.as_view()),
    path("verify-email/", VerifyEmailView.as_view()),

    # ADMIN
    path("admin/users/", AdminUsersView.as_view()),
    path("admin/delete-user/<int:user_id>/", AdminDeleteUserView.as_view()),
    path("admin/import-users-csv/", AdminImportUsersCSVView.as_view()),
]
