from django import forms

class GetCode(forms.Form):
    code = forms.Textarea()
    problem_id = forms.IntegerField()
    language_id = forms.IntegerField()
    custom_testcase = forms.CharField(max_length=300, required=False)

class PassProblemID(forms.Form):
    problem_id = forms.IntegerField()