from django.contrib import admin
from .models import Character, UserCharacter

# Register your models here.
admin.site.register(Character)
admin.site.register(UserCharacter)