from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from cats.models import Cat
from .models import Tag, CatTag
from .serializers import TagSerializer, AssignTagSerializer
from .permissions import IsAuthenticatedOrReadOnly


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("id")
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CatTagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        cat = get_object_or_404(Cat, pk=pk)

        if cat.owner != request.user:
            return Response({"error": "Только владелец имеет доступ"}, status=403)

        serializer = AssignTagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tags = serializer.validated_data["tags"]

        existing = set(cat.cat_tags.values_list("tag_id", flat=True))

        added = []
        skipped = []

        for tag_id in tags:
            if tag_id in existing:
                skipped.append(tag_id)
                continue

            if cat.cat_tags.count() >= 5:
                return Response(
                    {"error": "Нельзя больше 5 тегов"},
                    status=400
                )

            CatTag.objects.create(cat=cat, tag_id=tag_id)
            added.append(tag_id)

        return Response({
            "status": "updated",
            "added": added,
            "skipped": skipped
        }, status=200)

    @action(detail=False, methods=["get"])
    def filter_by_tag(self, request):
        tag_id = request.query_params.get("tag")

        if not tag_id:
            return Response({"error": "Необходимо указать тег"}, status=400)

        cats = Cat.objects.filter(cat_tags__tag_id=tag_id).distinct()

        return Response([
            {"id": c.id, "name": c.name}
            for c in cats
        ])

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        cat = get_object_or_404(Cat, pk=pk)

        tags = CatTag.objects.filter(cat=cat).values_list("tag_id", flat=True)

        similar = (
            Cat.objects
            .exclude(id=cat.id)
            .filter(cat_tags__tag_id__in=tags)
            .annotate(
                similarity=Count(
                    "cat_tags",
                    filter=Q(cat_tags__tag_id__in=tags)
                )
            )
            .order_by("-similarity")[:5]
        )

        return Response([
            {"id": c.id, "name": c.name, "similarity": c.similarity}
            for c in similar
        ])

    @action(detail=True, methods=["get"])
    def cat_tags(self, request, pk=None):
        cat = get_object_or_404(Cat, pk=pk)

        tags = Tag.objects.filter(tag_cats__cat=cat)

        return Response(TagSerializer(tags, many=True).data)
    
    @action(detail=True, methods=["delete"], url_path="remove/(?P<tag_id>[^/.]+)")
    def remove(self, request, pk=None, tag_id=None):
        cat = get_object_or_404(Cat, pk=pk)

        if cat.owner != request.user:
            return Response({"error": "Только владелец имеет доступ"}, status=403)

        deleted = CatTag.objects.filter(cat=cat, tag_id=tag_id).delete()

        if deleted[0] == 0:
            return Response({"error": "Тег не найден"}, status=404)

        return Response(status=204)
        
    @action(detail=True, methods=["put"])
    def replace(self, request, pk=None):
        cat = get_object_or_404(Cat, pk=pk)

        if cat.owner != request.user:
            return Response({"error": "Только владелец имеет доступ"}, status=403)

        tags = request.data.get("tags", [])

        if not tags:
            return Response({"error": "Пустой список"}, status=400)

        if len(tags) > 5:
            return Response({"error": "Максимум 5 тегов"}, status=400)

        if len(set(tags)) != len(tags):
            return Response({"error": "Дубликаты"}, status=400)

        existing = Tag.objects.filter(id__in=tags).count()
        if existing != len(tags):
            return Response({"error": "Некоторые теги не существуют"}, status=400)

        CatTag.objects.filter(cat=cat).delete()

        CatTag.objects.bulk_create([
            CatTag(cat=cat, tag_id=t) for t in tags
        ])

        return Response({"status": "replaced"})
