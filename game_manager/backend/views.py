from django.http import HttpResponse, JsonResponse
from django.core import serializers

from .models import Game, Release, Platform, Genre

def healthcheck(request):
    return HttpResponse("ok")

def index(request):
    games_list = Game.objects.all()
    res = '<h1>Game Manager</h1>'
    for game in games_list:
        res += f'<div><h2>{game}</h2>'

        # if we are the base for a collection...
        collectees = game.collectees.all();
        if collectees.count() > 0:
            res += '<div>I am a collection, I contain:<ul>'
            for collectee in collectees:
                res += f'<li>{collectee.title}</li>'
            res += '</ul></div>'

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
        dlc = game.dlc.all()
        if dlc.count() > 0:
            res += '<div>I have DLC:<ul>'
            for d in dlc:
                res += f'<li>{d.title}</li>'
            res += '</ul></div>'
        
        
        res += "</div>"

    return HttpResponse(res)