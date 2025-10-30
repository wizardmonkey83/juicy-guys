from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from .models import Profile, Submission
from .forms import SignUpForm, LoginForm, ChangeUsernameForm, UploadProfilePictureForm

from problems.models import UserProblem

# Create your views here.

# USER AUTHENTICATION ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def signup_view(request):

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            # TODO you're gonna need to figure out how to display this error within the signup form itself
            if User.objects.filter(Q(username=username) | Q(email=email)).exists():
                messages.error(request, "Username and/or Email already exists")

            user = form.save()
            login(request, user)
            return redirect("user_home")
        
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})

# so that user profiles will be created if they login through github
@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("user_home")
            else:
                # not sure if this is the best method for displaying errors unless the message can pop up without reloading or taking the user to another page.
                messages.error(request, "Invalid Username or Password")
            
    else:
        form = LoginForm()
    
    return render(request, "accounts/login.html", {"form": form})

# CHANGING STUFF -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@login_required
def change_username(request):
    if request.method == "POST":
        form = ChangeUsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            user = request.user

            username_exists = User.objects.filter(username=username).exists()
            if username_exists:
                # TODO implement logic for this
                messages.error(request, "Username Exists")
            else:
                user.username = username
                user.save()
                # TODO implement logic for this
                messages.success(request, "Username Changed")
        else:
            # TODO implement logic for this
            messages.error(request, "Invalid Form")

@login_required
def upload_profile_picture(request):
    if request.method == "POST":
        form = UploadProfilePictureForm(request.POST)
        if form.is_valid():
            picture = form.cleaned_data["picture"]
            user = request.user

            user.profile.profile_picture.delete()
            user.profile.profile_picture = picture
            user.profile.save()


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

# TODO remember to have a confirmation page built into this ("Are you sure you want to delete your account")
@login_required
def delete_account(request):
    user = request.user
    user.delete()
    return redirect("signup")

# LOADING PAGES ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
def profile_window(request):
    user = request.user
    # flat=True returns list of one item tuples. "ozuna" instead of ("ozuna",). can only be used hwen querying for one field
    languages_solved = Submission.objects.filter(user=user, status="Accepted").values_list("language__name", flat=True).distinct()
    categories_solved = UserProblem.objects.filter(user=user, status="solved").values_list("problem__category__name", flat=True).distinct()
    total_active_days = Submission.objects.filter(user=user).values("date_submitted__date").distinct().count()
    # slice can be changed for aesthetics
    recent_submissions = Submission.objects.filter(user=user).order_by("-date_submitted")[:10]
    return render(request, "accounts/profile.html", {"languages": languages_solved, "categories_solved": categories_solved, "total_active_days": total_active_days, "recent_submissions": recent_submissions})




