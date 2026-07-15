from rest_framework import serializers
from news.models import NewsChannel, NewsItem


class NewsChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsChannel
        fields = '__all__'


class NewsItemSerializer(serializers.ModelSerializer):
    pub_date = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = NewsItem
        fields = ['id', 'title', 'pub_date', 'source', 'link', 'is_favorite']

    def get_pub_date(self, obj):
        return obj.pub_date.strftime('%Y년 %m월 %d일')

    def get_is_favorite(self, obj):
        favorite_news_item_ids = self.context.get('favorite_news_item_ids', set())
        return obj.id in favorite_news_item_ids
