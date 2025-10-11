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
    
    def calculate_acceptance_rate(self):
        # TODO create logic for calculating acceptance rate
        return 

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Submission(models.Model):
    STATUS_CHOICES = [
        ("blank", "Blank"),
        ("accepted", "Accepted"),
        ("denied", "Denied"),
        ("time-limit-exceeded", "Time Limit Exceeded"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    code = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="blank")
    # to catch error outputs from judge0
    output = models.TextField()

    def __str__(self):
        return 


    