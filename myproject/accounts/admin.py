from django.contrib import admin
from .models import Profile, Badge, Submission

# Register your models here.
admin.site.register(Profile)
admin.site.register(Badge)
admin.site.register(Submission)