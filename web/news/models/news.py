from django.db import models
from news.models.common import BaseModel


class NewsChannel(BaseModel):
    generator = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=500)
    link = models.URLField(max_length=1000)
    language = models.CharField(max_length=10)
    web_master = models.EmailField(max_length=255, blank=True, null=True)
    copyright = models.TextField(blank=True, null=True)
    last_build_date = models.DateTimeField(blank=True, null=True)
    image_title = models.CharField(max_length=500, blank=True, null=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    image_link = models.URLField(max_length=1000, blank=True, null=True)
    image_height = models.IntegerField(blank=True, null=True)
    image_width = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class NewsItem(BaseModel):
    channel = models.ForeignKey(NewsChannel, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=500)
    link = models.URLField(max_length=1000)
    guid = models.CharField(max_length=1000, unique=True)
    pub_date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-pub_date']
