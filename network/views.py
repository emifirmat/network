import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import User, Post, Follow, Like
from .forms import PostForm


def paginate_posts(request, posts):
    """Function to paginate posts"""
    # Paginate
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    return posts

def get_liked_posts(request):
    if request.user.is_authenticated:
        return Like.objects.filter(user=request.user).values_list("post",
            flat=True)
    else: 
        return 

def index(request):
    """Main page, it shows all the posts and it let create a new one"""
    posts = Post.objects.all().order_by("-created_at")
    posts = paginate_posts(request, posts)
    liked_posts = get_liked_posts(request)
    
    # If a post is submited
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            new_post = Post(content=form.cleaned_data['content'],
                creator=request.user)
            new_post.save()
            return HttpResponseRedirect(reverse("network:index"))  
    
    # Regular load
    else:  
        form = PostForm()

    return render(request, "network/index.html", {
        "form": form,
        "posts": posts,
        "liked_posts": liked_posts,
    })


def profile(request, user_id):
    """Show profile of a selected user"""
    profile_user = User.objects.get(pk=user_id)
    
    # Determine if request user is following profile user or no
    if profile_user.followers_list.filter(user_following=request.user.id).exists():
        profile_user.is_following = True
    else:
        profile_user.is_following = False
    
    posts = Post.objects.filter(creator=user_id).order_by("-created_at")
    posts = paginate_posts(request, posts)
    liked_posts = get_liked_posts(request)

    return render(request, "network/profile.html", {
        "profile_user": profile_user,
        "posts": posts,
        "liked_posts": liked_posts,
    })


@login_required
def following(request):
    """Show posts from following users"""
    # Get user's following list
    following_list = Follow.objects.filter(
        user_following=request.user.id).values_list("user_followed")
    # Get posts filtered by user's following list
    posts = Post.objects.filter(
        creator__in=following_list).order_by("-created_at")
    posts = paginate_posts(request, posts)
    liked_posts = get_liked_posts(request)

    return render(request, "network/following.html", {
        "posts": posts,
        "liked_posts": liked_posts,
    })


@login_required
def follow(request):
    """Update following button"""
    if request.method == "POST":
        data = json.loads(request.body)
        user_to_follow = User.objects.get(pk=int(data['user_to_follow']))
        # Follow someone
        if data['follow'].strip() == "Follow": 
            follow = Follow(user_following=request.user,
                user_followed=user_to_follow)
            follow.follow_is_valid()
            follow.save()
            message = "Following"
        # Unfollow someone
        else:
            unfollow = Follow.objects.get(user_following=request.user,
                user_followed=user_to_follow)
            unfollow.delete()
            message = "Unfollowing"
        result = {
            "message": message,
        }
        return JsonResponse(result)
    else:
        return JsonResponse({"message": "Method should be POST"})


@login_required
def edit_post(request, post_id):
    """Modify the content of a post"""
    if request.method == "PUT":
        post = Post.objects.get(pk=post_id)
        data = json.loads(request.body)
        post.content = data['content']
        post.save()
        return JsonResponse({"message": "Post modified succesfully"})
    else:
        return JsonResponse({"message": "Method should be PUT"})


@login_required
def like_post(request, post_id):
    """Like or unlike a post"""
    if request.method == "POST":
        post = Post.objects.get(pk=post_id)
        # Like a coment
        try:
            like = Like(user=request.user, post=post)
            like.save()
            message = "liked"
        except IntegrityError:
            like = Like.objects.get(user= request.user, post=post)
            like.delete()
            message = "unliked"

        likes_count = Like.objects.filter(post=post).aggregate(
            Count("id"))["id__count"]
        return JsonResponse({
            "message": message,
            "likesCount": likes_count,
            }) 
    else:
        return JsonResponse({"message": "You should use request method POST"})


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("network:index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("network:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("network:index"))
    else:
        return render(request, "network/register.html")
