from django.http import HttpResponse, JsonResponse
from django.core import serializers

from .models import Game, Release, Platform, Genre, GameDlc, GameCollection

def healthcheck(request):
    return HttpResponse("ok")

def index(request):
    games_list = Game.objects.all()
    res = '<h1>Game Manager</h1>'
    for game in games_list:
        res += f'<div><h2>{game}</h2>'

        # if we are the base for a collection...
        collection = GameCollection.objects.filter(containingGame=game)
        if collection.count() > 0:
            for collect in collection:
                collectionGames = collect.containedGames
                res += f'I am a collection, and I contain: {", ".join(g.title for g in collectionGames.all())}'

        # developer(s)
        if game.developers.all().count() > 0:
            res += f'<div>by: {", ".join(g.name for g in game.developers.all())}</div>'

        # people
        if game.directors.all().count() > 0:
            res += f'<div>director(s): {",".join(p.name for p in game.directors.all())}</div>'

        # genres
        if game.genres.all().count() > 0:
            res += f'<div><span>{", ".join(g.name for g in game.genres.all())}</span></div>'

        # releases
        releases = Release.objects.filter(game=game)
        for release in releases:
            platforms = release.platforms.all()
            publishers = release.publishers.all()
            res += f'<div>&emsp;released on {release.release_date} for {" & ".join(plat.name for plat in platforms)} in {release.region.display_name} by {" & ".join(pub.name for pub in publishers)}</div>'
        
        # has dlc
        dlcs = GameDlc.objects.filter(baseGame=game)
        if dlcs.count() > 0:
            res += '<h3>DLC</h3>'
        for dlc in dlcs:
            res += f'<div>{dlc.dlcGame}</div>'
        
        
        res += "</div>"

    return HttpResponse(res)