from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef
from django.http import HttpResponse

from .models import Character, UserCharacter
from .forms import PassCharacterLevel, SearchForCharacter, FilterCategories

from problems.models import Category

# Create your views here.
@login_required
def character_list_window(request):
    user = request.user
    categories = Category.objects.all()

    user_characters = UserCharacter.objects.filter(user=user, character=OuterRef("pk"))
    all_characters = Character.objects.annotate(problems_solved_count=Subquery(user_characters.values("problems_solved_count")[:1]), user_level=Subquery(user_characters.values("level")[:1]))
    return render(request, "characters/characters.html", {"all_characters": all_characters, "categories": categories})


@login_required
def search_for_character(request):
    if request.method == "POST":
        form = SearchForCharacter(request.POST)
        if form.is_valid():
            user = request.user
            query = form.cleaned_data["query"]
            user_characters = UserCharacter.objects.filter(user=user, character=OuterRef("pk"))
            characters = Character.objects.filter(display_name__icontains=query).annotate(problems_solved_count=Subquery(user_characters.values("problems_solved_count")[:1]), user_level=Subquery(user_characters.values("level")[:1]))
            return render(request, "characters/search_character_fragment.html", {"characters": characters})
    return HttpResponse("")

@login_required
def filter_character_level(request):
    if request.method == "POST":
        form = PassCharacterLevel(request.POST)
        if form.is_valid():
            user = request.user
            level = form.cleaned_data["level"]
            if level == "all":
                user_characters = UserCharacter.objects.filter(user=user, character=OuterRef("pk"))
                characters = Character.objects.annotate(problems_solved_count=Subquery(user_characters.values("problems_solved_count")[:1]), user_level=Subquery(user_characters.values("level")[:1]))
                return render(request, "characters/filter_characters_fragment.html", {"characters": characters})
            else:
                user_characters = UserCharacter.objects.filter(user=user, level=level)
                return render(request, "characters/filter_characters_fragment.html", {"user_characters": user_characters})
                                                                                                                
@login_required
def filter_character_categories(request):
    if request.method == "POST":
        form = FilterCategories(request.POST)
        if form.is_valid():
            category_id = form.cleaned_data["category_id"]
            user = request.user
            if category_id == "all":
                user_characters = UserCharacter.objects.filter(user=user, character=OuterRef("pk"))
                characters = Character.objects.annotate(problems_solved_count=Subquery(user_characters.values("problems_solved_count")[:1]), user_level=Subquery(user_characters.values("level")[:1]))
                return render(request, "characters/filter_characters_fragment.html", {"characters": characters})
            else:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    # cant be bothered
                    pass
                user_characters = UserCharacter.objects.filter(user=user, character=OuterRef("pk"))
                characters = Character.objects.filter(category=category).annotate(problems_solved_count=Subquery(user_characters.values("problems_solved_count")[:1]), user_level=Subquery(user_characters.values("level")[:1]))
                return render(request, "characters/filter_characters_fragment.html", {"characters": characters})
