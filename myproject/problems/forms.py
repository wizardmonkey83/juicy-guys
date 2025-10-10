from django import forms

class GetCode(forms.Form):
    code = forms.Textarea()
    problem_id = forms.IntegerField()
    language_id = forms.IntegerField()