import requests
import json
import uuid
import time
import os
from decouple import config

# .env 파일에서 API 키와 URL을 안전하게 불러옵니다.
API_URL = config('CLOVA_OCR_APIGW_URL')
SECRET_KEY = config('CLOVA_OCR_SECRET_KEY')


def call_clova_ocr(image_file_path, file_format='jpeg'):
    """
    네이버 클로바 OCR API를 호출하여 이미지 내 템플릿 기반 텍스트를 추출하는 함수
    :param image_file_path: 분석할 이미지 파일의 경로
    :param file_format: 이미지 파일의 포맷 (jpg, jpeg, png 등)
    :return: 성공 시 {"success": True, "data": parsed_data}, 실패 시 {"success": False, "error": ...}
    """
    request_json = {
        'images': [
            {
                'format': file_format,
                'name': 'dorm_verification'  # 템플릿 이름과 일치시키면 좋습니다.
            }
        ],
        'requestId': str(uuid.uuid4()),
        'version': 'V2',
        'timestamp': int(round(time.time() * 1000))
    }

    payload = {'message': json.dumps(request_json).encode('UTF-8')}
    files = [
        ('file', open(image_file_path, 'rb'))
    ]
    headers = {
        'X-OCR-SECRET': SECRET_KEY
    }

    try:
        # 네이버 클로바 OCR 서버에 POST 요청을 보냅니다.
        response = requests.post(API_URL, headers=headers, data=payload, files=files, timeout=5)
        response.raise_for_status()  # HTTP 200번대가 아니면 예외를 발생시킵니다.

        result = response.json()

        # 응답이 성공적인지 확인합니다.
        if result['images'][0]['inferResult'] != 'SUCCESS':
            return {"success": False, "error": result['images'][0]['message']}

        # OCR 결과에서 필요한 데이터만 파싱하여 딕셔너리로 만듭니다.
        parsed_data = {}
        for field in result['images'][0]['fields']:
            field_name = field.get('name')
            field_text = field.get('inferText')
            if field_name:
                parsed_data[field_name] = field_text

        return {"success": True, "data": parsed_data}

    except requests.exceptions.RequestException as e:
        # 네트워크 오류나 타임아웃 등 통신 오류 발생 시
        return {"success": False, "error": f"API 요청 중 오류 발생: {e}"}

