from django.db import models
from django.contrib.auth import get_user_model
from cats.models import Cat

User = get_user_model()


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    cat = models.ForeignKey(Cat, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'cat'], name='unique_favorite')
        ]
