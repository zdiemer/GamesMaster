from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Platform(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}"

class Region(models.Model):
    display_name = models.CharField(max_length=200)
    short_code = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.display_name}"

class People(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}"

class Company(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}"

class Franchise(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}"

class Game(models.Model):
    title = models.CharField(max_length=200)
    genres = models.ManyToManyField(Genre)
    franchises = models.ManyToManyField(Franchise)
    developers = models.ManyToManyField(Company)

    def __str__(self):
        return f"{self.title}"

class Release(models.Model):
    platforms = models.ManyToManyField(Platform())
    release_date = models.DateField()
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    game = models.ForeignKey(Game, on_delete=models.PROTECT)
    publishers = models.ManyToManyField(Company)
