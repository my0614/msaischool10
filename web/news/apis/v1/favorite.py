from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from news.models import Favorite, NewsItem
from news.serializers.favorite import FavoriteSerializer


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # 앱(RN 클라이언트)은 CSRF 토큰을 다루지 않으므로 세션 인증에서 검사를 건너뛴다.


class FavoriteListView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user).select_related('news_item')
        serializer = FavoriteSerializer(favorites, many=True)
        return Response(dict(status='OK', message='SUCCESS', data=serializer.data))

    def post(self, request):
        news_item_id = request.data.get('news_item_id')
        try:
            news_item = NewsItem.objects.get(id=news_item_id)
        except (NewsItem.DoesNotExist, ValueError):
            return Response(
                dict(status='ERROR', message='뉴스를 찾을 수 없습니다.', data={}), status=404
            )

        favorite, _ = Favorite.objects.get_or_create(user=request.user, news_item=news_item)
        serializer = FavoriteSerializer(favorite)
        return Response(dict(status='OK', message='SUCCESS', data=serializer.data))


class FavoriteDetailView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, news_item_id):
        favorite = Favorite.objects.filter(user=request.user, news_item_id=news_item_id).first()
        if not favorite:
            return Response(
                dict(status='ERROR', message='즐겨찾기를 찾을 수 없습니다.', data={}), status=404
            )
        favorite.delete()
        return Response(dict(status='OK', message='SUCCESS', data={}))
