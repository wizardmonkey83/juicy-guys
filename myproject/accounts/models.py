from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem, Language

# Create your models here.
class Badge(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField()
    short_description = models.CharField(max_length=100)
    long_description = models.TextField()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    badges = models.ManyToManyField(Badge, on_delete=models.PROTECT)
    
    profile_picture = models.ImageField(default="avatar.jpg", upload_to="profile_pictures")
    problems_solved_count = models.PositiveIntegerField(default=0)
    submissions_made_count = models.PositiveIntegerField(default=0)
    
    def calculate_acceptance_rate(self):
        # TODO create logic for calculating acceptance rate
        return 

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    code = models.TextField()
    testcases_passed = models.PositiveIntegerField()
    num_of_testcases = models.PositiveIntegerField()
    status = models.CharField(max_length=100)
    # this may be an incorrect format
    runtime = models.PositiveIntegerField()
    memory = models.PositiveIntegerField()
    # i think this adds the date automatically when its created....
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 


    