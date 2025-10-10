from django.db import models

# Create your models here.
class Category(models.Model):
    # math, system-design, hashing, etc
    name = models.CharField(max_length=100)

class Language(models.Model):
    name = models.CharField(max_length=100)
    judge0_id = models.PositiveIntegerField()

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
    starting_code = models.TextField()
    recommended_time_complexity = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    language = models.ManyToManyField(Language, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class TestCase(models.Model):
    input_data = models.TextField()
    expected_output = models.TextField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="testcases")

    def __str__(self):
        return f"Testcase for {self.problem.title}"

class Hint(models.Model):
    hint = models.TextField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="hints")

    def __str__(self):
        return f"Hint for {self.problem.title}"

class Solution(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="solutions")
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    time_complexity = models.CharField(max_length=150)
    code = models.TextField()
    description = models.TextField()

