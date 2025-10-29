from django.urls import path
from .views import character_list_window, filter_character_level, search_for_character, filter_character_categories

urlpatterns = [
    # load page
    path("characters/", character_list_window, name="character_list_window"),

    # filtering
    path("characters/filter-level/", filter_character_level, name="filter_character_level"),
    path("characters/filter-category/", filter_character_categories, name="filter_character_categories"),
    path("characters/search/", search_for_character, name="search_for_character"),

]