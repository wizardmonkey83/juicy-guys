from django.contrib import admin
from .models import Category, Language, Problem, TestCase, Hint, Solution, UserProblem, Quote, Example, SolutionCode, ExampleTestcase, ProblemCode

# Register your models here.
admin.site.register(Category)
admin.site.register(Language)
admin.site.register(Problem)
admin.site.register(TestCase)
admin.site.register(Hint)
admin.site.register(Solution)
admin.site.register(UserProblem)
admin.site.register(Quote)
admin.site.register(Example)
admin.site.register(SolutionCode)
admin.site.register(ExampleTestcase)
admin.site.register(ProblemCode)