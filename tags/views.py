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

        serializer = AssignTagSerializer(
            data=request.data,
            context={"cat": cat}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"status": "tags assigned"}, status=201)

    @action(detail=False, methods=["get"])
    def filter_by_tag(self, request):
        tag_id = request.query_params.get("tag")

        if not tag_id:
            return Response({"error": "tag required"}, status=400)

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
