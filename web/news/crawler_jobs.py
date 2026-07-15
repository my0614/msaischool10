import threading
import time
import traceback

from news.crewler.news import parse_and_save_rss_feed_with_feedparser

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/?hl=ko&gl=KR&ceid=KR:ko"
CRAWL_INTERVAL_SECONDS = 10 * 60


def _run_forever():
    while True:
        try:
            parse_and_save_rss_feed_with_feedparser(GOOGLE_NEWS_RSS_URL)
        except Exception:
            traceback.print_exc()
        time.sleep(CRAWL_INTERVAL_SECONDS)


def start_background_crawler():
    thread = threading.Thread(target=_run_forever, daemon=True)
    thread.start()
