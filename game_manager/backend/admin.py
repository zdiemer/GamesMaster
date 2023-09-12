from django.contrib import admin

from .models import Game, GameDlc, Genre, Platform, Release, Person

admin.site.register(Game)
admin.site.register(GameDlc)
admin.site.register(Genre)
admin.site.register(Platform)
admin.site.register(Release)
admin.site.register(Person)