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
    notable_developers = models.ManyToManyField(Person, through="NotableDeveloper")

    # Self many-to-many references.
    # Setting this will imply that the games in this list are DLC, and that THIS game is the "parent" game.
    dlc = models.ManyToManyField(
        "self", symmetrical=False, related_name="%(class)s_dlc"
    )
    # Setting this will imply that this game is a "collection" of other games.
    collectees = models.ManyToManyField(
        "self", symmetrical=False, related_name="%(class)s_collectees"
    )

    # TODO
    # engine
    # mode: singleplayer, co-op, multiplayer
    # logical-sequel/prequel (put into franchise (?))

    def __str__(self):
        return f"{self.title}"


class NotableDeveloper(models.Model):
    developer = models.ForeignKey(Person, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    role = models.CharField(max_length=200)


class Release(models.Model):
    platforms = models.ManyToManyField(Platform())
    release_date = models.DateField()
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    game = models.ForeignKey(Game, on_delete=models.PROTECT)
    publishers = models.ManyToManyField(Company)
