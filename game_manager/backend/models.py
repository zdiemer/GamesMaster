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


class Person(models.Model):
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

    # People
    directors = models.ManyToManyField(Person, related_name="%(class)s_directors")
    composers = models.ManyToManyField(Person, related_name="%(class)s_composers")

    def __str__(self):
        return f"{self.title}"


class GameDlc(models.Model):
    baseGame = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="%(class)s_base_game"
    )
    dlcGame = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="%(class)s_dlc_game"
    )


class GameCollection(models.Model):
    # this should be unique
    containingGame = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="%(class)s_containing_game"
    )
    containedGames = models.ManyToManyField(
        Game, related_name="%(class)s_contained_games"
    )


class Release(models.Model):
    platforms = models.ManyToManyField(Platform())
    release_date = models.DateField()
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    game = models.ForeignKey(Game, on_delete=models.PROTECT)
    publishers = models.ManyToManyField(Company)
