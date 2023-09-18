from backend.models import (
    Game,
    Genre,
    Platform,
    Region,
    Company,
    Franchise,
    Release,
    Person,
    NotableDeveloper,
    Mode,
)


def run():
    # I must be made prior to use, because I have more than just a name field.
    naRegion, _ = Region.objects.get_or_create(
        display_name="North America", short_code="NA"
    )

    games = [
        {
            "title": "BioShock",
            "genres": ["First-Person Shooter", "SystemShock-Like"],
            "franchises": ["BioShock"],
            "developers": ["2K Boston", "2K Australia"],
            "modes": ["Singleplayer"],
            "notableDevelopers": [
                {
                    "name": "Ken Levine",
                    "role": "director",
                },
                {
                    "name": "Ken Levine",
                    "role": "writer",
                },
                {
                    "name": "Garry Schyman",
                    "role": "composer",
                },
            ],
            "releases": [
                {
                    "release_date": "2007-08-21",
                    "region": "NA",
                    "publishers": ["2K Games"],
                    "platforms": ["Xbox 360", "PC"],
                },
                {
                    "release_date": "2008-10-21",
                    "region": "NA",
                    "publishers": ["2K Games"],
                    "platforms": ["PS3"],
                },
                {
                    "release_date": "2009-10-01",
                    "region": "NA",
                    "publishers": ["Feral Interactive"],
                    "platforms": ["MacOS"],
                },
            ],
        },
        {
            "title": "BioShock 2",
            "genres": ["First-Person Shooter", "SystemShock-Like"],
            "franchises": ["BioShock"],
            "developers": ["2K Marin"],
            "modes": ["Singleplayer", "Multiplayer"],
            "notableDevelopers": [
                {
                    "name": "Jordan Thomas",
                    "role": "director",
                },
            ],
            "releases": [
                {
                    "release_date": "2010-02-09",
                    "region": "NA",
                    "publishers": ["2K Games"],
                    "platforms": ["Xbox 360", "PC", "PS3"],
                },
            ],
        },
        {
            "title": "BioShock 2: Minerva's Den",
            "genres": ["First-Person Shooter", "SystemShock-Like"],
            "franchises": ["BioShock"],
            "developers": ["2K Marin"],
            "notableDevelopers": [],
            "modes": ["Singleplayer"],
            "releases": [
                {
                    "release_date": "2010-08-31",
                    "region": "NA",
                    "publishers": ["2K Games"],
                    "platforms": ["Xbox 360", "PS3"],
                },
            ],
            "dlc_of": "BioShock 2",
        },
        {
            "title": "BioShock Infinite: Industrial Revolution",
            "genres": ["Puzzle"],
            "franchises": ["BioShock"],
            "developers": ["Lazy 8 Studios"],
            "modes": ["Singleplayer"],
            "notableDevelopers": [
                {
                    "name": "Joshua Davis",
                    "role": "UX Developer",
                },
                {
                    "name": "Jorge Lacera",
                    "role": "Art Director",
                },
            ],
            "releases": [
                {
                    "release_date": "2013-01-24",
                    "region": "NA",
                    "publishers": ["2K Games"],
                    "platforms": ["PC"],
                },
            ],
        },
        {
            "title": "BioShock Infinite",
            "genres": ["First-Person Shooter", "SystemShock-Like"],
            "franchises": ["BioShock"],
            "developers": ["Irrational Games"],
            "modes": ["Singleplayer"],
            "notableDevelopers": [
                {
                    "name": "Ken Levine",
                    "role": "director",
                },
            ],
            "releases": [
                {
                    "release_date": "2013-03-26",
                    "region": "NA",
                    "publishers": ["2K Games"],
                    "platforms": ["Xbox 360", "PC", "PS3"],
                },
            ],
        },
        {
            "title": "BioShock: The Collection",
            "genres": ["First-Person Shooter", "SystemShock-Like"],
            "franchises": ["BioShock"],
            "developers": ["Blind Squirrel Games"],
            "notableDevelopers": [],
            "modes": ["Singleplayer"],
            "releases": [
                {
                    "release_date": "2016-09-13",
                    "region": "NA",
                    "publishers": ["2K Games"],
                    "platforms": ["Xbox 360", "PS3"],
                },
            ],
            "collection_of": ["BioShock", "BioShock 2", "BioShock Infinite"],
        },
    ]

    for g in games:
        dbg = Game(title=g["title"])
        dbg.save()

        for genre in g["genres"]:
            dbGenre, _ = Genre.objects.get_or_create(name=genre)
            dbg.genres.add(dbGenre)

        for franchise in g["franchises"]:
            fdb, _ = Franchise.objects.get_or_create(name=franchise)
            dbg.franchises.add(fdb)

        for developers in g["developers"]:
            dbDev, _ = Company.objects.get_or_create(name=developers)
            dbg.developers.add(dbDev)

        for nd in g["notableDevelopers"]:
            personDb, _ = Person.objects.get_or_create(name=nd["name"])
            NotableDeveloper.objects.create(
                developer=personDb, game=dbg, role=nd["role"]
            )

        for m in g["modes"]:
            mDb, _ = Mode.objects.get_or_create(mode=m)
            dbg.modes.add(mDb)

        for r in g["releases"]:
            rls, _ = Release.objects.get_or_create(
                release_date=r["release_date"],
                region=Region.objects.get(short_code=r["region"]),
                game=dbg,
            )
            for pub in r["publishers"]:
                pubDb, _ = Company.objects.get_or_create(name=pub)
                rls.publishers.add(pubDb)
            for plat in r["platforms"]:
                platDb, _ = Platform.objects.get_or_create(name=plat)
                rls.platforms.add(platDb)

        if "dlc_of" in g:
            # we are a dlc game.
            owner = Game.objects.get(title=g["dlc_of"])
            owner.dlc.add(dbg)

        if "collection_of" in g:
            # we are a collection of other games.
            for collectee in g["collection_of"]:
                dbg.collectees.add(Game.objects.get(title=collectee))

        dbg.save()
