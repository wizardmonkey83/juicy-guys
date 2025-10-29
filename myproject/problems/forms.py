from django import forms

class GetCode(forms.Form):
    code = forms.CharField()
    problem_id = forms.IntegerField()
    language_id = forms.IntegerField()
    custom_testcases = forms.CharField()

class SearchForProblem(forms.Form):
    query = forms.CharField(max_length=200)

class FilterProblemDifficulty(forms.Form):
    difficulty = forms.CharField(max_length=20)

class PassProblemID(forms.Form):
    problem_id = forms.IntegerField()

class FilterCategories(forms.Form):
    category_id = forms.CharField()