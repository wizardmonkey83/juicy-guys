from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef
from django.http import HttpResponse

from .models import Character, UserCharacter
from .forms import PassCharacterLevel, SearchForCharacter

from problems.models import Category

# Create your views here.
@login_required
def character_list_window(request):
    user = request.user
    categories = Category.objects.all()
    user_level = UserCharacter.objects.filter(character=OuterRef("pk"), user=user).values("level")[:1]
    all_characters = Character.objects.annotate(user_level=Subquery(user_level))
    return render(request, "characters/characters.html", {"all_characters": all_characters, "categories": categories})


@login_required
def search_for_character(request):
    if request.method == "POST":
        form = SearchForCharacter(request.POST)
        if form.is_valid():
            user = request.user
            query = form.cleaned_data["query"]
            user_level = UserCharacter.objects.filter(character=OuterRef("pk"), user=user).values("level")[:1]
            characters = Character.objects.filter(display_name__icontains=query).annotate(user_level=Subquery(user_level))
            return render(request, "characters/search_character_fragment.html", {"characters": characters})
    return HttpResponse("")

@login_required
def filter_character_level(request):
    if request.method == "POST":
        form = PassCharacterLevel(request.POST)
        if form.is_valid():
            user = request.user
            level = form.cleaned_data["level"]
            user_character_level = UserCharacter.objects.filter(character=OuterRef("pk"), user=user, level=level).values("problems_solved_count")[:1]
            filtered_characters = Character.objects.annotate(user_character_status=Subquery(user_character_level))
            return render(request, "characters/filter_characters_fragment.html", {"filtered_charactes": filtered_characters})