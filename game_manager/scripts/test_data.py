from backend.models import Game, GameDlc, Genre, Platform, Region, Company, Franchise, Release, Person, GameCollection


def run():
    xbox360, _ = Platform.objects.get_or_create(name="Xbox 360")
    pc, _ = Platform.objects.get_or_create(name="PC")
    ps3, _ = Platform.objects.get_or_create(name="PS3")
    fpsGenre, _ = Genre.objects.get_or_create(name="First-Person Shooter")
    sslGenre, _ = Genre.objects.get_or_create(name="SystemShock-Like")
    naRegion, _ = Region.objects.get_or_create(display_name="North America", short_code="NA")
    twoK, _ = Company.objects.get_or_create(name="2K Games")
    twoKBoston, _ = Company.objects.get_or_create(name="2K Boston")
    twoKAustralia, _ = Company.objects.get_or_create(name="2K Australia")
    twoKMarin, _ = Company.objects.get_or_create(name="2K Marin")
    blindSquirrel, _ = Company.objects.get_or_create(name="Blind Squirrel Games")
    bioshockFranchise, _ = Franchise.objects.get_or_create(name="BioShock")

    # people
    kenLevine, _ = Person.objects.get_or_create(name="Ken Levine")


    Release.objects.all().delete()
    Game.objects.all().delete()

    # BioShock 1
    bioshock = Game(
        title="BioShock",
    )
    bioshock.save()
    bioshock.genres.set([fpsGenre, sslGenre])
    bioshock.franchises.set([bioshockFranchise])
    bioshock.developers.set([twoKBoston, twoKAustralia])
    bioshock.directors.set([kenLevine])
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

    # BioShock 2
    bioshockTwo = Game(
        title="BioShock 2",
    )
    bioshockTwo.save()
    bioshockTwo.genres.set([fpsGenre, sslGenre])
    bioshockTwo.franchises.set([bioshockFranchise])
    bioshockTwo.developers.set([twoKMarin])

    bioshockTwo.save()

    bsTwoInitialRelease = Release(
        release_date="2010-02-09",
        region=naRegion,
        game=bioshockTwo,
    )
    bsTwoInitialRelease.save()
    bsTwoInitialRelease.publishers.set([twoK])
    bsTwoInitialRelease.platforms.set([xbox360, pc, ps3])
    bsTwoInitialRelease.save()

    # BioShock 2 Minerva's Den
    bioshockTwoMinerva = Game(
        title="BioShock 2: Minerva's Den",
    )
    bioshockTwoMinerva.save()
    bioshockTwoMinerva.genres.set([fpsGenre, sslGenre])
    bioshockTwoMinerva.franchises.set([bioshockFranchise])
    bioshockTwoMinerva.developers.set([twoKMarin])
    bioshockTwoMinerva.save()

    bsTwoMinervaInitialRelease = Release(
        release_date="2010-08-31",
        region=naRegion,
        game=bioshockTwoMinerva,
    )
    bsTwoMinervaInitialRelease.save()
    bsTwoMinervaInitialRelease.publishers.set([twoK])
    bsTwoMinervaInitialRelease.platforms.set([xbox360, ps3])
    bsTwoMinervaInitialRelease.save()

    # Assocaite Bioshock 2 with it's DLC
    GameDlc.objects.create(baseGame=bioshockTwo, dlcGame=bioshockTwoMinerva)
    
    # Bioshock the collection
    bsCollect = Game(
        title="BioShock: The Collection",
    )
    bsCollect.save()
    bsCollect.developers.set([blindSquirrel])
    bsCollect.save()

    # Associate collection with 1 & 2.
    collection, _ = GameCollection.objects.get_or_create(containingGame=bsCollect)
    collection.save()

    collection.containedGames.set([bioshock, bioshockTwo])

    bsCollectionRls = Release(
        release_date="2016-09-13",
        region=naRegion,
        game=bsCollect,
    )
    bsCollectionRls.save()
    bsCollectionRls.publishers.set([twoK])
    bsCollectionRls.platforms.set([xbox360, ps3])
    bsCollectionRls.save()
