from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem, Language

from datetime import datetime, timedelta

# Create your models here.
class Badge(models.Model):
    title = models.CharField(max_length=100)
    image_path = models.CharField(max_length=200)
    short_description = models.CharField(max_length=100)
    long_description = models.TextField()

    def __str__(self):
        return f"{self.title}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    badges = models.ManyToManyField(Badge)
    
    profile_picture = models.ImageField(default="avatar.jpg", upload_to="profile_pictures")
    problems_solved_count = models.PositiveIntegerField(default=0)
    submissions_made_count = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    max_streak = models.PositiveIntegerField(default=0)
    last_submission_date = models.DateField(null=True, blank=True)
    
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

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    code = models.TextField()
    testcases_passed = models.PositiveIntegerField()
    num_of_testcases = models.PositiveIntegerField()
    # message returned by judge0
    status = models.CharField(max_length=100)
    # this may be an incorrect format
    runtime = models.PositiveIntegerField()
    memory = models.PositiveIntegerField()
    # i think this adds the date automatically when its created....
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.problem.title} - {self.date_submitted}"


    