from django.http import JsonResponse
from rest_framework.views import APIView
from news.models import Favorite, NewsItem
from news.serializers.news import NewsItemSerializer

class NewsItemListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        news_items = NewsItem.objects.all().order_by('-pub_date')

        favorite_news_item_ids = set()
        if request.user.is_authenticated:
            favorite_news_item_ids = set(
                Favorite.objects.filter(user=request.user).values_list('news_item_id', flat=True)
            )

        serializer = NewsItemSerializer(
            news_items, many=True, context={'favorite_news_item_ids': favorite_news_item_ids}
        )
        return JsonResponse({
        'status': 'OK',
        'message': '뉴스 아이템 목록을 성공적으로 불러왔습니다.',
        'data': serializer.data
        })
