from django.urls import path
from .views import character_list_window, filter_character_level, search_for_character

urlpatterns = [
    # load page
    path("characters/", character_list_window, name="character_list_window"),

    # filtering
    path("characters/filter/", filter_character_level, name="filter_character_level"),
    path("characters/search/", search_for_character, name="search_for_character"),

]