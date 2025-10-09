from django.contrib import admin
from .models import Category, Language, Problem, TestCase, Hint

# Register your models here.
admin.site.register(Category)
admin.site.register(Language)
admin.site.register(Problem)
admin.site.register(TestCase)
admin.site.register(Hint)