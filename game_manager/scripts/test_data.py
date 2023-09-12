from backend.models import Game, Genre, Platform, Region, Company, Franchise, Release


def run():
    xbox360, _ = Platform.objects.get_or_create(name="Xbox 360")
    pc, _ = Platform.objects.get_or_create(name="PC")
    ps3, _ = Platform.objects.get_or_create(name="PS3")
    fpsGenre, _ = Genre.objects.get_or_create(name="First-Person Shooter")
    sslGenre, _ = Genre.objects.get_or_create(name="SystemShock-Like")
    naRegion, _ = Region.objects.get_or_create(display_name="North America", short_code="NA")
    twoK, _ = Company.objects.get_or_create(name="2K Games")
    bioshockFranchise, _ = Franchise.objects.get_or_create(name="BioShock")

    Release.objects.all().delete()
    Game.objects.all().delete()

    bioshock = Game(
        title="BioShock",
    )
    bioshock.save()
    bioshock.genres.set([fpsGenre, sslGenre])
    bioshock.franchises.set([bioshockFranchise])
    bioshock.developers.set([twoK])
    bioshock.save()

    bsInitialRelease = Release(
        release_date="2007-08-21",
        region=naRegion,
        game=bioshock,
    )
    bsInitialRelease.save()
    bsInitialRelease.publishers.set([twoK])
    bsInitialRelease.platforms.set([xbox360, pc])
    bsInitialRelease.save()

    bsPsFollowupRelease = Release(
        release_date="2008-10-21",
        region=naRegion,
        game=bioshock,
    )
    bsPsFollowupRelease.save()
    bsPsFollowupRelease.publishers.set([twoK])
    bsPsFollowupRelease.platforms.set([ps3])
    bsPsFollowupRelease.save()


    
