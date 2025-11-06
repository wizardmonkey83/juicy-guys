from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from .models import Profile, Submission, Badge
from .forms import SignUpForm, LoginForm, ChangeUsernameForm, UploadProfilePictureForm, EditProfileForm

from problems.models import UserProblem, Problem, Category
from characters.models import Character, UserCharacter

import random

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
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect("problem_list_window")
        
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})

# so that user profiles will be created if they login through github
@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        # so that the cards appear as not achieved
        characters = Character.objects.all()
        for character in characters:
            UserCharacter.objects.create(user=instance, character=character, level="blank", problems_solved_count=0) 

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("problem_list_window")
            else:
                # not sure if this is the best method for displaying errors unless the message can pop up without reloading or taking the user to another page.
                form.add_error(None, "Invalid Username or Password")
            
    else:
        form = LoginForm()
    
    return render(request, "accounts/login.html", {"form": form})

# CHANGING STUFF -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
    return redirect("login_view")

# TODO remember to have a confirmation page built into this ("Are you sure you want to delete your account")
@login_required
def delete_account_warning(request):
    return render(request, "accounts/profile/delete_account_warning.html")

@login_required
def delete_account(request):
    user = request.user
    user.delete()
    return redirect("signup_view")

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

    badges = Badge.objects.all()

    solved_easy = UserProblem.objects.filter(user=user, problem__difficulty="easy", status="solved").count()
    solved_medium = UserProblem.objects.filter(user=user, problem__difficulty="medium", status="solved").count()
    solved_hard = UserProblem.objects.filter(user=user, problem__difficulty="hard", status="solved").count()
    solved_legendary = UserProblem.objects.filter(user=user, problem__difficulty="legendary", status="solved").count()

    total_solved = {
        "solved_easy": solved_easy,
        "solved_medium": solved_medium,
        "solved_hard": solved_hard,
        "solved_legendary": solved_legendary
    }

    total_easy_problems = Problem.objects.filter(difficulty="easy").count()
    total_medium_problems = Problem.objects.filter(difficulty="medium").count()
    total_hard_problems = Problem.objects.filter(difficulty="hard").count()
    total_legendary_problems = Problem.objects.filter(difficulty="legendary").count()

    total_problems = {
        "total_easy": total_easy_problems,
        "total_medium": total_medium_problems,
        "total_hard": total_hard_problems,
        "total_legendary": total_legendary_problems
    }

    context = {
        "languages": languages_solved, 
        "categories": categories_solved, 
        "total_active_days": total_active_days, 
        "recent_submissions": recent_submissions,
        "total_problems": total_problems,
        "total_solved": total_solved,
        "badges": badges
    }

    return render(request, "accounts/profile/profile.html", context)

@login_required
def edit_profile_options(request):
    return render(request, "accounts/profile/edit_profile_options.html")

@login_required
def load_badges_fragment(request):
    badges = Badge.objects.all()
    return render(request, "accounts/profile/badges_fragment.html", {"badges": badges})

@login_required
def save_edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            profile_picture = request.FILES.get("profile_picture")
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            old_password = form.cleaned_data["old_password"]
            password1 = form.cleaned_data["password1"]
            password2 = form.cleaned_data["password2"]

            if profile_picture:
                user.profile.profile_picture = profile_picture
            if username:
                username_exists = User.objects.filter(username=username).exists()
                if not username_exists and username != user.username:
                    user.username = username
                    user.save()
            if email:
                if user.email != email:
                    user.email = email
                    user.save()
            if old_password:
                if user.check_password(old_password):
                    if password1 and password2 and password1 == password2:
                        user.set_password(password1)
                        user.save()
            login(request, user)
            badges = Badge.objects.all()
            return render(request, "accounts/profile/badges_fragment.html", {"badges": badges})


# INDEX/ABOUT PAGES ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def load_about(request):
    return render(request, "about.html")

def load_index(request):
    all_characters = Character.objects.all()
    # so levels look dynamic
    numbers = random.sample(range(1, 101), 30)
    categories = Category.objects.all()
    return render(request, "index.html", {"all_characters": all_characters, "numbers": numbers, "categories": categories})
