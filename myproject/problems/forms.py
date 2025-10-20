from django import forms

class GetCode(forms.Form):
    code = forms.Textarea()
    problem_id = forms.IntegerField()
    language_id = forms.IntegerField()
    custom_testcase = forms.CharField(max_length=300, required=False)

class SearchForProblem(forms.Form):
    query = forms.CharField(max_length=200)

class FilterProblemDifficulty(forms.Form):
    difficulty = forms.CharField(max_length=20)