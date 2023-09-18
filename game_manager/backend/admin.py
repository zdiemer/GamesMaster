from django.contrib import admin

from .models import Game, Genre, Platform, Release, Person

admin.site.register(Game)
admin.site.register(Genre)
admin.site.register(Platform)
admin.site.register(Release)
admin.site.register(Person)