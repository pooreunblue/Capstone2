import requests
import json
import uuid
import time
import os
from decouple import config

API_URL = config('CLOVA_OCR_APIGW_URL')
SECRET_KEY = config('CLOVA_OCR_SECRET_KEY')
TEMPLATE_ID = config('CLOVA_OCR_TEMPLATE_ID')

def parse_admission_status(text):
    """
    "25-1학기 선발\n(학기)" 와 같은 문자열을 파싱하여 학기와 거주 기간을 분리합니다.
    """
    try:
        parts = text.split('\n')
        semester_part = parts[0].replace('선발', '').strip()
        period_part = parts[1]

        if '학기' in period_part:
            residency_period = 'SEMESTER'
        elif '6개월' in period_part:
            residency_period = 'SIXMONTHS'
        else:
            residency_period = None

        return semester_part, residency_period
    except (IndexError, AttributeError):
        return None, None

def call_clova_ocr(image_file_path):
    """
    네이버 클로바 OCR API를 호출하여 이미지 내 템플릿 기반 텍스트를 추출하는 함수
    :param image_file_path: 분석할 이미지 파일의 경로
    :return: 성공 시 {"success": True, "data": parsed_data}, 실패 시 {"success": False, "error": ...}
    """
    request_body = {
        'version': 'V2',
        'requestId': str(uuid.uuid4()),
        'timestamp': int(time.time() * 1000),
        'images': [
            {
                'format': os.path.splitext(image_file_path)[1].lstrip('.'),  # 파일 확장자 동적 추출
                'name': 'dorm_verification',  # 템플릿을 식별하기 위한 이름
                'templateIds': [int(TEMPLATE_ID)]  # .env에서 불러온 템플릿 ID 사용
            }
        ]
    }

    headers = {
        'X-OCR-SECRET': SECRET_KEY
    }

    files = [
        ('message', (None, json.dumps(request_body), 'application/json')),
        ('file', open(image_file_path, 'rb'))
    ]

    try:
        response = requests.post(API_URL, headers=headers, files=files, timeout=10)
        response.raise_for_status()

        result = response.json()

        if result['images'][0]['inferResult'] != 'SUCCESS':
            return {"success": False, "error": result['images'][0].get('message', 'OCR 추론에 실패했습니다.')}

        parsed_data = {}
        for field in result['images'][0]['fields']:
            field_name = field.get('name')
            field_text = field.get('inferText', '').strip()
            if field_name:
                parsed_data[field_name] = field_text

        return {"success": True, "data": parsed_data}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API 요청 중 오류 발생: {e}"}