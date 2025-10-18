from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.db.models import Q

from django.contrib.auth.models import User
from .models import Profile
from .forms import SignUpForm, LoginForm, ChangeUsernameForm, UploadProfilePictureForm


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
            # creates profile model alongside the user
            Profile.objects.create(user=user)
            login(request, user)
            return redirect("user_home")
        
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})

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
    
    return render(request, "registration/login.html", {"form": form})

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

