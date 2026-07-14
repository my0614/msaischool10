from django.urls import path, re_path
from news.apis.v1.common import HelloWorldView, SampleListView, SampleDetailView
urlpatterns = [
path(r'helloworld/', HelloWorldView.as_view(), name='helloWorld'),
path(r'samples/', SampleListView.as_view(), name='sampleList'),
path(r'samples/<uuid:sample_id>/', SampleDetailView.as_view(), name='sampleDetail'),
]