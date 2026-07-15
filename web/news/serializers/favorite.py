from rest_framework import serializers
from news.models import Favorite
from news.serializers.news import NewsItemSerializer


class FavoriteSerializer(serializers.ModelSerializer):
    news_item = NewsItemSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'news_item', 'created_at']
