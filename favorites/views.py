from django.db import IntegrityError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Favorite
from .serializers import FavoriteSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        cat = serializer.validated_data['cat']

        if cat.owner == self.request.user:
            raise ValidationError("Нельзя добавить своего кота")

        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError("Этот кот уже в избранном")
