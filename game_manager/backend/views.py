from django.http import HttpResponse, JsonResponse
from django.core import serializers

from .models import Game, Release, Platform, Genre, NotableDeveloper, Purchase

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
        
        # has dlc
        dlc = game.dlc.all()
        if dlc.count() > 0:
            res += '<div>I have DLC:<ul>'
            for d in dlc:
                res += f'<li>{d.title}</li>'
            res += '</ul></div>'


        # developer(s)
        if game.developers.all().count() > 0:
            res += f'<div>Developed by: {", ".join(g.name for g in game.developers.all())}</div>'

        # people
        devs = NotableDeveloper.objects.filter(game=game)
        if devs.count() > 0:
            for dev in devs.all():
                res += f'<div>&emsp;{dev.role}: {dev.developer.name}</div>'

        # genres
        if game.genres.all().count() > 0:
            res += f'<div><span>{", ".join(g.name for g in game.genres.all())}</span></div>'

        if game.modes.all().count() > 0:
            res += f'<div><span>{", ".join(g.mode for g in game.modes.all())}</span></div>'

        # releases
        releases = Release.objects.filter(game=game)
        for release in releases:
            platforms = release.platforms.all()
            publishers = release.publishers.all()
            res += f'<div>&emsp;released on {release.release_date} for {" & ".join(plat.name for plat in platforms)} in {release.region.display_name} by {" & ".join(pub.name for pub in publishers)}</div>'

        res += "</div>"
    
    purchased_games = Purchase.objects.all()
    res += '<h1>Games in Collection</h1>'
    for purchase in purchased_games:
        game = purchase.release.game
        res += f"<div><h2>{game.title}</h2>"
        res += f"<div>purchased for: ${purchase.purchase_price} on {purchase.purchase_date} in {purchase.get_purchase_format_display()}</div>"
        res += f""

        res += "</div>"


    return HttpResponse(res)