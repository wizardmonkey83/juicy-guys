from django.urls import path
from .views import signup_view, login_view, profile_window, edit_profile_options, logout_view, delete_account_warning, save_edit_profile, load_badges_fragment, delete_account, load_about

urlpatterns = [
    # registration
    path("signup/", signup_view, name="signup_view"),
    path("login/", login_view, name="login_view"),

    # profile
    path("profile/", profile_window, name="profile_window"),
    path("profile/edit-options/", edit_profile_options, name="edit_profile_options"),
    path("profile/save/", save_edit_profile, name="save_edit_profile"),
    path("profile/load-badges/", load_badges_fragment, name="load_badges_fragment"),
    path("profile/logout/", logout_view, name="logout_view"),
    path("profile/delete-warning/", delete_account_warning, name="delete_account_warning"),
    path("profile/delete/", delete_account, name="delete_account"),

    # about
    path("about/", load_about, name="load_about"),
]