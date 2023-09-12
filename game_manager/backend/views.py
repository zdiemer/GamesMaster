from django.http import HttpResponse, JsonResponse
from django.core import serializers

from .models import Game, Release, Platform, Genre

def index(request):
    games_list = Game.objects.all()
    res = '<h1>Game Manager</h1>'
    for game in games_list:
        res += f'<div>{game}</div>'

        # developer(s)
        res += f'<div>by: {", ".join(g.name for g in game.developers.all())}</div>'

        # genres
        genres = Genre.objects.filter(game=game).values("name")
        res += f'<div><span>{", ".join(g["name"] for g in list(genres))}</span></div>'

        # releases
        releases = Release.objects.filter(game=game)
        for release in releases:
            platforms = release.platforms.all()
            res += f'<div>&emsp;released on {release.release_date} for {" & ".join(plat.name for plat in platforms)} in {release.region.display_name}</div>'

    return HttpResponse(res)