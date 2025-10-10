from django.urls import path
from .views import process_code

urlpatterns = [
    path("problems/problem/run", process_code, name="process_code"),

]