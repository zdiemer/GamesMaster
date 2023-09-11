from backend.models import Game, Genre, Platform


def run():
    xbox360, _ = Platform.objects.get_or_create(name="Xbox 360")
    xboxone, _ = Platform.objects.get_or_create(name="Xbox One")
    genre, _ = Genre.objects.get_or_create(name="first-person-shooter")

    Game.objects.all().delete()

    game = Game(
        title="BioShock",
    )

    game.save()

    game.genres.set([genre])
    game.platforms.set([xbox360, xboxone])

    game.save()
    
