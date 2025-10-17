from django.db import models
from django.contrib.auth.models import User
from problems.models import Category

# Create your models here.

class Character(models.Model):
    STATUS_CHOICES = [
        ("unknown", "Unknown"),
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
        ("legendary", "Legendary"),
    ]
    name = models.CharField(max_length=100)
    # a simulated biography 
    description = models.TextField()
    image = models.ImageField()
    difficulty = models.CharField(choices=STATUS_CHOICES, default="unknown", max_length=20)
    # .PROTECT raises a warning if a cateogry linked to characters is deleted 
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

class UserCharacter(models.Model):
    STATUS_CHOICES = [
        ("blank", "Not Attempted"),
        ("bronze", "Bronze"),
        ("silver", "Silver"),
        ("gold", "Gold"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="characters")
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=STATUS_CHOICES, default="blank")
    problems_solved_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s copy of {self.character.name}"