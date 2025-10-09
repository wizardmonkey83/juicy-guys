from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.db.models import Q

from django.contrib.auth.models import User
from .models import Profile
from .forms import SignUpForm, LoginForm


# Create your views here.
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
        form = LoginForm()
    
    return render(request, "registration/login.html", {"form": form})
        
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def delete_account(request):
    user = request.user

    user.delete()
    return redirect("signup")