from django.urls import path
from news.apis.v1.news import NewsItemListAPIView
urlpatterns = [
path('', NewsItemListAPIView.as_view(), name='news'),]