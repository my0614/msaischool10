from django.http import JsonResponse
from rest_framework.views import APIView
from news.models import NewsItem
from news.serializers.news import NewsItemSerializer

class NewsItemListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        news_items = NewsItem.objects.all().order_by('-pub_date')
        serializer = NewsItemSerializer(news_items, many=True)
        return JsonResponse({
        'status': 'OK',
        'message': '뉴스 아이템 목록을 성공적으로 불러왔습니다.',
        'data': serializer.data
        })