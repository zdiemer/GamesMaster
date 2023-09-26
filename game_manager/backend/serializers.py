from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import (
    Game,
    Genre,
    Release,
    Company,
    Mode,
    Platform,
    Purchase,
    NotableDeveloper,
    Franchise,
    Review,
)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name", "url_slug"]


class FranchiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name", "url_slug"]


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
        fields = ["url_slug", "name"]


class PurchaseSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer()

    class Meta:
        model = Purchase
        fields = [
            "purchase_format",
            "purchase_date",
            "purchase_price",
            "platform",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    platforms = PlatformSerializer(many=True)

    class Meta:
        model = Review
        fields = [
            "reviewing_agency",
            "notes",
            "rating",
            "platforms",
        ]


class ReleaseSerializer(serializers.ModelSerializer):
    region = serializers.SlugRelatedField(read_only=True, slug_field="display_name")
    platforms = PlatformSerializer(many=True)
    publishers = CompanySerializer(many=True)
    reviews = ReviewSerializer(many=True, source="review_set")
    purchases = PurchaseSerializer(many=True, source="purchase_set")

    class Meta:
        model = Release
        fields = [
            "release_date",
            "platforms",
            "region",
            "publishers",
            "reviews",
            "purchases",
        ]


class NotableDeveloperSerializer(serializers.ModelSerializer):
    name = serializers.SlugRelatedField(
        source="developer", read_only=True, slug_field="name"
    )

    class Meta:
        model = NotableDeveloper
        fields = [
            "name",
            "role",
        ]


class GameListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    developers = CompanySerializer(many=True, read_only=True)
    franchises = FranchiseSerializer(many=True, read_only=True)

    # releases = ReleaseSerializer(source='release_set', many=True, read_only=True)
    modes = serializers.SlugRelatedField(many=True, read_only=True, slug_field="mode")

    class Meta:
        model = Game
        fields = [
            "url_slug",
            "title",
            "genres",
            "developers",
            "modes",
            "franchises",
        ]

    def create(self, validated_data):
        g = Game.objects.create(**validated_data)
        return g


class NestedGameSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    developers = CompanySerializer(many=True)
    franchises = FranchiseSerializer(many=True)

    # releases = ReleaseSerializer(source='release_set', many=True, read_only=True)
    modes = serializers.SlugRelatedField(many=True, read_only=True, slug_field="mode")

    class Meta:
        model = Game
        fields = [
            "url_slug",
            "title",
            "genres",
            "developers",
            "modes",
            "franchises",
        ]


class GameDetailSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    developers = CompanySerializer(many=True)
    franchises = FranchiseSerializer(many=True)
    modes = serializers.SlugRelatedField(many=True, read_only=True, slug_field="mode")
    dlc = NestedGameSerializer(many=True)
    collectees = NestedGameSerializer(many=True)

    notable_developers = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "url_slug",
            "title",
            "cover_art_uuid",
            "genres",
            "developers",
            "modes",
            "franchises",
            "dlc",
            "collectees",
            "notable_developers",
            # "releases",
        ]

    def get_notable_developers(self, instance):
        nds = NotableDeveloper.objects.filter(game=instance)
        return [NotableDeveloperSerializer(nd).data for nd in nds]
