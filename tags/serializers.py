from rest_framework import serializers
from .models import Tag, CatTag
from cats.models import Cat


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class CatTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatTag
        fields = ["id", "cat", "tag"]


class AssignTagSerializer(serializers.Serializer):
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Список тегов пуст")

        existing = Tag.objects.filter(id__in=value).count()

        if existing != len(value):
            raise serializers.ValidationError("Некоторые теги не существуют")

        return value

    def create(self, validated_data):
        cat = self.context["cat"]
        tags = validated_data["tags"]

        result = []

        for tag_id in tags:
            obj, _ = CatTag.objects.get_or_create(
                cat=cat,
                tag_id=tag_id
            )
            result.append(obj)

        return result
