from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
            
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", )
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
            "email": forms.TextInput(attrs={"placeholder": "Email"}),
            "password1": forms.PasswordInput(attrs={"placeholder": "Password"}),
            "password2": forms.PasswordInput(attrs={"placeholder": "Re-enter Password"}),
        }
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}))

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=100, required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

class ChangeUsernameForm(forms.Form):
    username = forms.CharField(max_length=100)

class UploadProfilePictureForm(forms.Form):
    picture = forms.ImageField()