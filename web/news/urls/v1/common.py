from django.urls import path, re_path
from news.apis.v1.common import HelloWorldView
urlpatterns = [
path(r'helloworld/', HelloWorldView.as_view(), name='helloWorld'),
]