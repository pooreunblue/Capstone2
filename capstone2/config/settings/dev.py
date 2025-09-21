# config/settings/dev.py
from .base import * # 기본 설계도의 모든 내용을 가져옵니다.

# 개발 환경에서는 모든 IP의 접속을 허용합니다.
ALLOWED_HOSTS = ['*']

# 여기에 개발용 데이터베이스 설정 등을 추가할 수 있습니다.