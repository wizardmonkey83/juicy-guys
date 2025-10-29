from django import forms

class PassCharacterLevel(forms.Form):
    level = forms.CharField(max_length=50)

class SearchForCharacter(forms.Form):
    query = forms.CharField(max_length=100)

class FilterCategories(forms.Form):
    category_id = forms.CharField()