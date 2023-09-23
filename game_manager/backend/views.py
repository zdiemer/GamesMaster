from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions, status, generics
from django.contrib.postgres.aggregates import ArrayAgg
from minio import Minio
import os 
from PIL import Image
import io

from .serializers import GenreSerializer, CompanySerializer, ModeSerializer, PlatformSerializer, GameListSerializer, GameDetailSerializer, ReleaseSerializer
from .models import Game, Release, Platform, Genre, NotableDeveloper, Purchase, Company, Mode

minioClient = Minio(
    "minio:9000",
    access_key=os.environ.get("MINIO_ROOT_USER"),
    secret_key=os.environ.get("MINIO_ROOT_PASSWORD"),
    secure=False,
)

def healthcheck(request):
    return HttpResponse("ok")

def serveImage(request, image_id):
    response = None
    data = None
    # try:
    response = minioClient.get_object(
        os.environ.get("MINIO_DEFAULT_BUCKET"),
        image_id,
    )
    data = response.data
    im = Image.open(io.BytesIO(data))
    s = im.size
    # take in the height as a param.
    ratio = 200/s[1]
    newimg = im.resize((int(s[0]*ratio), int(s[1]*ratio)), Image.Resampling.LANCZOS)
    
    if data == None:
        return HttpResponse(f"failed to fetch")
    else:
        img_byte_arr = io.BytesIO()
        newimg.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return HttpResponse(img_byte_arr, content_type="image/png")


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


class ReleaseList(generics.ListCreateAPIView):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer

class CompanyList(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class GenreList(generics.ListCreateAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ModeList(generics.ListCreateAPIView):
    queryset = Mode.objects.all()
    serializer_class = ModeSerializer


class PlatformList(generics.ListCreateAPIView):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


class GameList(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameListSerializer

    def get_queryset(self):
        queryset = self.queryset
        collections_only = self.request.query_params.get('collections_only')
        if collections_only:
            return queryset.exclude(collectees=None)
        else:
            return queryset.filter(game_dlc=None).filter(collectees=None).order_by("title")


class GameDetailList(generics.RetrieveUpdateDestroyAPIView):
    queryset = Game.objects.all()
    serializer_class = GameDetailSerializer


class GameRelease(viewsets.ModelViewSet):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        queryset = self.queryset
        query_set = queryset.filter(game=pk)
        return query_set
