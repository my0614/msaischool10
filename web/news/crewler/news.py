import os
import sys
import django
import feedparser
from datetime import datetime
import pytz
# 현재 스크립트 파일의 절대 경로 (예: /path/to/kc-news-back-service/news/crawlers/news.py)
script_path = os.path.abspath(__file__)
# 현재 스크립트가 위치한 디렉토리 (예: /path/to/kc-news-back-service/news/crawlers/)
current_dir = os.path.dirname(script_path)
# 앱 루트 디렉토리 (예: /path/to/kc-news-back-service/news/)
# news/crawlers/ 에서 news/ 로 이동
app_root = os.path.dirname(current_dir)
# 프로젝트 루트 디렉토리 (예: /path/to/kc-news-back-service/)
# news/ 에서 kc-news-back-service/ 로 이동
project_root = os.path.dirname(app_root)
# Python 모듈 검색 경로의 맨 앞에 프로젝트 루트 디렉토리를 추가합니다.
sys.path.insert(0, project_root)


# Django 설정 파일 경로 지정
# 'project'는 settings.py를 포함하는 내부 폴더 이름입니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
# Django 환경 초기화
django.setup()
# --- Django 환경 설정 끝 ---
# Django 모델 임포트 (Django 환경 설정 후에 임포트해야 함)
from news.models import NewsChannel, NewsItem


def parse_and_save_rss_feed_with_feedparser(rss_url):
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        print(f"경고: 피드 파싱이 불완전할 수 있습니다: {feed.bozo_exception}")

    if not feed.feed:
        print("오류: 피드 데이터가 없습니다 (유효하지 않은 URL이거나 빈 피드일 수 있습니다).")
        return

    feed_info = feed.feed
    channel_data = {
        'generator': feed_info.get('generator'),
        'title': feed_info.get('title'),
        'link': feed_info.get('link'),
        'language': feed_info.get('language'),
        'web_master': feed_info.get('webmaster'),
        'copyright': feed_info.get('rights'),
        'description': feed_info.get('subtitle'),
    }
    if 'published_parsed' in feed_info and feed_info.published_parsed:
        try:
            dt_object = datetime(*feed_info.published_parsed[:6])
            channel_data['last_build_date'] = pytz.utc.localize(dt_object)
        except Exception as e:
            print(f"경고: last_build_date '{feed_info.published_parsed}'를 파싱할 수 없습니다: {e}")
            channel_data['last_build_date'] = None
    elif 'updated_parsed' in feed_info and feed_info.updated_parsed:
        try:
            dt_object = datetime(*feed_info.updated_parsed[:6])
            channel_data['last_build_date'] = pytz.utc.localize(dt_object)
        except Exception as e:
            print(f"경고: updated_parsed '{feed_info.updated_parsed}'를 파싱할 수 없습니다: {e}")
            channel_data['last_build_date'] = None
    else:
        channel_data['last_build_date'] = None

    if 'image' in feed_info and feed_info.image:
        image_info = feed_info.image
        channel_data['image_title'] = image_info.get('title')
        channel_data['image_url'] = image_info.get('href')
        channel_data['image_link'] = image_info.get('link')
        channel_data['image_height'] = None
        channel_data['image_width'] = None

    channel, created = NewsChannel.objects.update_or_create(
        link=channel_data['link'],
        defaults=channel_data
    )
    if created:
        print(f"새 채널 생성: {channel.title}")
    else:
        print(f"기존 채널 업데이트: {channel.title}")

    for entry in feed.entries:
        item_data = {
            'channel': channel,
            'title': entry.get('title'),
            'link': entry.get('link'),
            'guid': entry.get('guid', entry.get('link')),
            'description': entry.get('summary'),
        }
        if hasattr(entry, 'source'):
            item_data['source'] = entry.source.get('title')
            item_data['source_url'] = entry.source.get('href')
        else:
            pass

        if 'published_parsed' in entry and entry.published_parsed:
            try:
                dt_object = datetime(*entry.published_parsed[:6])
                item_data['pub_date'] = pytz.utc.localize(dt_object)
            except Exception as e:
                print(f"경고: 항목 '{item_data.get('title', 'N/A')}'의 pub_date '{entry.published_parsed}'를 파싱할 수 없습니다: {e}")
                item_data['pub_date'] = None
        elif 'updated_parsed' in entry and entry.updated_parsed:
            try:
                dt_object = datetime(*entry.updated_parsed[:6])
                item_data['pub_date'] = pytz.utc.localize(dt_object)
            except Exception as e:
                print(f"경고: 항목 '{item_data.get('title', 'N/A')}'의 updated_parsed '{entry.updated_parsed}'를 파싱할 수 없습니다: {e}")
                item_data['pub_date'] = None
        else:
            item_data['pub_date'] = None

        if item_data['guid']:
            news_item, created_item = NewsItem.objects.update_or_create(
                guid=item_data['guid'],
                defaults=item_data
            )
            if created_item:
                print(f"새 뉴스 항목 추가: {news_item.title}")
        else:
            print(f"GUID가 없어 항목을 건너뜁니다: {item_data.get('title', 'N/A')}")


if __name__ == "__main__":
    google_news_rss_url = "https://news.google.com/rss/?hl=ko&gl=KR&ceid=KR:ko"
    parse_and_save_rss_feed_with_feedparser(google_news_rss_url)
    print("\n파싱 및 저장 완료!")
