from django.db import models
from cats.models import Cat


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class CatTag(models.Model):
    cat = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        related_name='cat_tags'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tag_cats'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cat', 'tag'],
                name='unique_cat_tag'
            )
        ]

    def __str__(self):
        return f"{self.cat} - {self.tag}"
