from PIL import Image
import uuid
from minio import Minio
import os
import json
import re

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
    Purchase,
    Review,
)


def convert_to_url_slug(slug: str) -> str:
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return re.sub(r'[^0-9a-zA-Z\-]+', '', slug)


def run():
    # I must be made prior to use, because I have more than just a name field.
    Region.objects.create(
        display_name="North America", short_code="NA"
    )
    Region.objects.create(
        display_name="Europe, Africa, and Asia", short_code="PAL"
    )
    Region.objects.create(
        display_name="Worldwide", short_code="WW"
    )
    games = []
    with open('/code/scripts_data/test_data.json', encoding="utf-8") as json_file:
        games_data = json.load(json_file)
        games = games_data["games"]

    minio_client = Minio(
        "minio:9000",
        access_key=os.environ.get("MINIO_ROOT_USER"),
        secret_key=os.environ.get("MINIO_ROOT_PASSWORD"),
        secure=False,
    )
    bucket_name = os.environ.get("MINIO_DEFAULT_BUCKET")

    for g in games:
        # Upload cover art to minio

        cover_art_uuid = "0000" # default art placeholder.

        if "cover_art_filepath" in g:
            minio_id = str(uuid.uuid4())

            result = minio_client.fput_object(
                bucket_name, minio_id, g["cover_art_filepath"],
            )
            print(
                "created {0} object; etag: {1}, version-id: {2}".format(
                    result.object_name, result.etag, result.version_id,
                ),
            )
            cover_art_uuid = minio_id

        url_slug = convert_to_url_slug(g["title"])

        dbg = Game(title=g["title"], cover_art_uuid=cover_art_uuid, url_slug=url_slug)
        dbg.save()

        if "genres" in g:
            for genre in g["genres"]:
                dbGenre, _ = Genre.objects.get_or_create(name=genre)
                dbg.genres.add(dbGenre)

        if "franchises" in g:
            for franchise in g["franchises"]:
                fdb, _ = Franchise.objects.get_or_create(name=franchise, url_slug=convert_to_url_slug(franchise))
                dbg.franchises.add(fdb)

        if "developers" in g:
            for developers in g["developers"]:
                dbDev, _ = Company.objects.get_or_create(name=developers, url_slug=convert_to_url_slug(developers))
                dbg.developers.add(dbDev)

        if "notableDevelopers" in g:
            for nd in g["notableDevelopers"]:
                personDb, _ = Person.objects.get_or_create(name=nd["name"])
                NotableDeveloper.objects.create(
                    developer=personDb, game=dbg, role=nd["role"]
                )

        if "modes" in g:
            for m in g["modes"]:
                mDb, _ = Mode.objects.get_or_create(mode=m)
                dbg.modes.add(mDb)

        if "releases" in g:
            for r in g["releases"]:
                rls, _ = Release.objects.get_or_create(
                    release_date=r["release_date"],
                    region=Region.objects.get(short_code=r["region"]),
                    game=dbg,
                )
                for pub in r["publishers"]:
                    pubDb, _ = Company.objects.get_or_create(name=pub, url_slug=convert_to_url_slug(pub))
                    rls.publishers.add(pubDb)
                for plat in r["platforms"]:
                    platDb, _ = Platform.objects.get_or_create(name=plat, url_slug=convert_to_url_slug(plat))
                    rls.platforms.add(platDb)
                
                if "purchases" in r:
                    for pur in r["purchases"]:
                        platDb, _ = Platform.objects.get_or_create(name=pur["platform"], url_slug=convert_to_url_slug(pur["platform"]))
                        pur["release"] = rls
                        pur["platform"] = platDb
                        Purchase.objects.create(
                            **pur
                        )
                
                if "reviews" in r:
                    for rev in r["reviews"]:
                        rev["release"] = rls
                        # rev["platforms"] = 
                        Review.objects.create(
                            **rev
                        )


        if "dlc_of" in g:
            # we are a dlc game.
            owner = Game.objects.get(title=g["dlc_of"])
            owner.dlc.add(dbg)

        if "collection_of" in g:
            # we are a collection of other games.
            for collectee in g["collection_of"]:
                dbg.collectees.add(Game.objects.get(title=collectee))

        dbg.save()
