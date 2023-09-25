from django.db import models
import uuid

class Genre(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f"{self.name}"


class Mode(models.Model):
    mode = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f"{self.mode}"


class Platform(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name}"


class Region(models.Model):
    display_name = models.CharField(max_length=200)
    short_code = models.CharField(max_length=10)

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
    url_slug = models.CharField(max_length=200, unique=True)
    # UUIDv4 to a minio image.
    cover_art_uuid = models.CharField(max_length=36)
    # If a game has been ported to a new engine, a new game entry should be created.
    engine = models.CharField(max_length=200)
    genres = models.ManyToManyField(Genre)
    franchises = models.ManyToManyField(Franchise)
    developers = models.ManyToManyField(Company)
    notable_developers = models.ManyToManyField(Person, through="NotableDeveloper")
    modes = models.ManyToManyField(Mode)

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
    # logical-sequel/prequel (put into franchise (?))
    # awards
    # reviews

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


class Purchase(models.Model):
    SEALED = "SL"
    COMPLETE = "CO"
    GAME_AND_BOX_ONLY = "GB"
    GAME_ONLY = "GO"
    OWNERSHIP_TYPE_CHOICES = [
        (SEALED, "Sealed"),
        (COMPLETE, "Complete"),
        (GAME_AND_BOX_ONLY, "Game and Box Only"),
        (GAME_ONLY, "Game Only"),
    ]
    ownership_type = models.CharField(
        max_length=2,
        choices=OWNERSHIP_TYPE_CHOICES,
    )

    BROKEN_BOX = "BB"
    SCRATCHES = "SC"
    STICKERS = "ST"

    CONDITION_CHOICES = [
        (BROKEN_BOX, "Broken Box"),
        (SCRATCHES, "Scratches"),
        (STICKERS, "Stickers"),
    ]
    condition_type = models.CharField(
        max_length=2,
        choices=CONDITION_CHOICES,
        null=True,
    )

    PHYSICAL = "PL"
    DIGITAL = "DG"
    PURCHASE_FORMAT_CHOICES = [
        (PHYSICAL, "Physical"),
        (DIGITAL, "Digital"),
    ]
    purchase_format = models.CharField(
        max_length=2,
        choices=PURCHASE_FORMAT_CHOICES,
    )

    purchase_date = models.DateField()
    purchase_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
    )

    release = models.ForeignKey(Release, on_delete=models.CASCADE)
