from django.core.management.base import BaseCommand

from news.crewler.news import parse_and_save_rss_feed_with_feedparser

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/?hl=ko&gl=KR&ceid=KR:ko"


class Command(BaseCommand):
    help = "구글 뉴스 RSS를 크롤링해 NewsItem을 갱신합니다."

    def handle(self, *args, **options):
        parse_and_save_rss_feed_with_feedparser(GOOGLE_NEWS_RSS_URL)
        self.stdout.write(self.style.SUCCESS("뉴스 크롤링 완료"))
