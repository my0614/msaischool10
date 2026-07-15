from django.urls import path, re_path
from news.apis.v1.common import HelloWorldView, SampleDetailView, SampleListView
from news.views import hello_world

urlpatterns = [
    path(r"helloworld/", HelloWorldView.as_view(), name="helloWorld"),
    path(r"helloworld2/", hello_world, name="helloWorld2"),
    path("samples/", SampleListView.as_view(), name="sample-list"),
    path(
        "samples/<uuid:sample_id>/", SampleDetailView.as_view(), name="sample-detail"
    ),
]