from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import Game, Genre, Release, Company, Mode, Platform


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name"]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["name"]


class ModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mode
        fields = ["mode"]


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ["name"]


class ReleaseSerializer(serializers.ModelSerializer):
    region = serializers.SlugRelatedField(read_only=True, slug_field="display_name")
    platforms = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )

    class Meta:
        model = Release
        fields = ["release_date", "platforms", "region"]


class GameSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    developers = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    franchises = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )

    # releases = ReleaseSerializer(source='release_set', many=True, read_only=True)
    modes = serializers.SlugRelatedField(many=True, read_only=True, slug_field="mode")

    class Meta:
        model = Game
        fields = [
            "url",
            "title",
            "genres",
            "developers",
            "modes",
            "franchises",
            # "releases",
        ]
