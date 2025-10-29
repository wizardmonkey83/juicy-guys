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
    display_name = models.CharField(max_length=100)
    technical_name = models.CharField(max_length=100)
    ability = models.TextField()
    ability_description = models.TextField()
    # a simulated biography. might introduce later on.
    long_description = models.TextField(blank=True)
    difficulty = models.CharField(choices=STATUS_CHOICES, default="unknown", max_length=20)
    # .PROTECT raises a warning if a cateogry linked to characters is deleted 
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.display_name

class UserCharacter(models.Model):
    STATUS_CHOICES = [
        ("blank", "Not Attempted"),
        ("bronze", "Bronze"),
        ("silver", "Silver"),
        ("gold", "Gold"),
        ("legendary", "Legendary"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="characters")
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=STATUS_CHOICES, default="blank")
    problems_solved_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s copy of {self.character.display_name}"