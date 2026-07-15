from django.urls import path
from news.apis.v1.news import NewsItemListAPIView
from news.apis.v1.favorite import FavoriteListView, FavoriteDetailView

urlpatterns = [
    path('', NewsItemListAPIView.as_view(), name='news'),
    path('favorites/', FavoriteListView.as_view(), name='favoriteList'),
    path('favorites/<uuid:news_item_id>/', FavoriteDetailView.as_view(), name='favoriteDetail'),
]
