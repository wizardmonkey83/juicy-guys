from django.contrib import admin
from .models import Category, UserCategory, UserCharacter

# Register your models here.
admin.site.register(Category)
admin.site.register(UserCategory)
admin.site.register(UserCharacter)