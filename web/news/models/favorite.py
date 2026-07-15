from django.conf import settings
from django.db import models

from news.models.common import BaseModel
from news.models.news import NewsItem


class Favorite(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites'
    )
    news_item = models.ForeignKey(
        NewsItem, on_delete=models.CASCADE, related_name='favorited_by'
    )

    class Meta:
        verbose_name = '즐겨찾기'
        verbose_name_plural = verbose_name
        unique_together = [('user', 'news_item')]

    def __str__(self):
        return f'{self.user} → {self.news_item}'
