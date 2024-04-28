
from django.urls import path

from . import views

app_name = "network"
urlpatterns = [
    # Index/All posts web page
    path("", views.index, name="index"),
    # User's profile page
    path("profile/<int:user_id>", views.profile, name="profile"),
    # Posts from following users page
    path("following", views.following, name="following"),
    # Edit posts
    path("edit_post/<int:post_id>", views.edit_post, name="edit_post"),
    # Like posts
    path("like_post/<int:post_id>", views.like_post, name="like_post"),
    # Accounts web pages
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    #API Routes
    path("follow", views.follow, name="follow"),
]
