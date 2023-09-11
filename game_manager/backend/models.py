from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Platform(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}"

class Game(models.Model):
    title = models.CharField(max_length=200)
    genres = models.ManyToManyField(Genre)
    platforms = models.ManyToManyField(Platform)

    def __str__(self):
        return f"{self.title}"
