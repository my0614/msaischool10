import os
import sys

from django.apps import AppConfig


class NewsConfig(AppConfig):
    name = 'news'

    def ready(self):
        if 'runserver' not in sys.argv:
            return
        # runserver는 자동 재시작(autoreload)을 위해 프로세스를 두 번 띄운다.
        # RUN_MAIN='true'인 실제 서버 프로세스에서만 시작해야 스케줄러가 중복 실행되지 않는다.
        if os.environ.get('RUN_MAIN') != 'true' and '--noreload' not in sys.argv:
            return

        from news.crawler_jobs import start_background_crawler
        start_background_crawler()
