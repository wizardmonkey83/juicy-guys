from django.db import models
from django.contrib.auth.models import User

# TODO you will need to add contraints, either as a new model or as a field within the problem model

# Create your models here.
class Category(models.Model):
    # math, system-design, hashing, etc
    name = models.CharField(max_length=100)
    icon_filename = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=100)
    judge0_id = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Problem(models.Model):
    STATUS_CHOICES = [
        ("unknown", "Unknown"),
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
        ("legendary", "Legendary"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unknown")
    recommended_time_complexity = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    problem_solved_count = models.PositiveIntegerField(default=0)
    submissions_made_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title
    
    def calculate_acceptance_rate(self):
        if self.submissions_made_count > 0:
            acceptance_rate = self.problem_solved_count / self.submissions_made_count
            acceptance_rate *= 100
            acceptance_rate = round(acceptance_rate, 1)
        else:
            acceptance_rate = 0
        return acceptance_rate
    
    @property
    def acceptance_rate(self):
        acceptance_rate = self.calculate_acceptance_rate()
        return acceptance_rate
    
class ProblemCode(models.Model):
    starting_code = models.TextField()                              # python. da
    language = models.ForeignKey(Language, on_delete=models.CASCADE, default=71)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="code")

    def __str__(self):
        return f"Starting Code for {self.problem.title} - {self.language.name}"

class TestCase(models.Model):
    input_data = models.TextField()
    expected_output = models.TextField()
    language = models.ManyToManyField(Language)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="testcases")

    def __str__(self):
        return f"Testcase for {self.problem.title}"

# this might not be needed, but fine for now. check back on it
class ExampleTestcase(models.Model):
    input_data = models.TextField()
    expected_output = models.TextField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="example_testcases")

    def __str__(self):
        return f"Example Testcase for {self.problem.title}"

class Hint(models.Model):
    hint = models.TextField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="hints")

    def __str__(self):
        return f"Hint for {self.problem.title}"

class Example(models.Model):
    input_data = models.TextField()
    # this has got to be faulty 
    output_data = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="examples")

    def __str__(self):
        return f"Example for {self.problem.title}"

class Solution(models.Model):
    title = models.CharField(max_length=100)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="solutions")
    time_complexity = models.CharField(max_length=150)
    space_complexity = models.CharField(max_length=150, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"Solution for {self.problem.title} - {self.title}"
    
class SolutionCode(models.Model):
    code = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name="codes")

    def __str__(self):
        return f"Code for {self.solution.title} - {self.solution.problem.title}"

class UserProblem(models.Model):
    STATUS_CHOICES = [
        ("blank", "Blank"),
        ("attempted", "Attempted"),
        ("solved", "Solved")
    ]
    status = models.CharField(choices=STATUS_CHOICES, default="blank", max_length=15)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="problems")

    def __str__(self):
        return f"{self.user.username} - {self.problem.title}"

class Quote(models.Model):
    quote = models.CharField(max_length=100)

    def __str__(self):
        return self.quote