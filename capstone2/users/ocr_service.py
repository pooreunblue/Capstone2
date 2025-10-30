from collections import defaultdict

import requests
import json
import uuid
import time
import os
import re
from decouple import config

API_URL = config('CLOVA_OCR_APIGW_URL')
SECRET_KEY = config('CLOVA_OCR_SECRET_KEY')

HEADER_KEYWORDS = ['학과', '학번', '학년', '이름', '성별', '지원건물', '지원호실구분', '합격여부', '등록여부', '대기순번']
STOP_KEYWORDS = [
    'TEL.', 'FAX.', 'Copyright', 'All rights reserved',
    '개인정보처리', '이메일수집거부', '|<', 'K', '>|'
]
X_TOLERANCE = 20
Y_STOP_PADDING = 5

def process_ocr_response_with_coords(result):
    """
    General OCR V2 응답의 'fields'와 'boundingPoly' 좌표를 기반으로
    수동으로 테이블을 재구성합니다. (v9.1 - Stop Boundary Padding)

    서비스에 맞게 print() 대신 dict를 return 합니다.
    """

    try:
        image = result['images'][0]
    except (IndexError, KeyError):
        return {"success": False, "error": "응답 형식이 예상과 다릅니다. 'images' 리스트를 찾을 수 없습니다."}

    if image['inferResult'] != 'SUCCESS':
        return {"success": False, "error": f"OCR 인식 실패: {image['message']}"}

    if 'fields' not in image or not image['fields']:
        return {"success": False, "error": "인식된 텍스트 필드가 없습니다."}

    # 1단계: API 필드 정규화
    all_fields = []
    for field in image['fields']:
        if 'boundingPoly' not in field or not field.get('inferText'):
            continue

        vertices = field['boundingPoly']['vertices']
        y_center = sum(v['y'] for v in vertices) / 4
        x_start = min(v['x'] for v in vertices)
        x_end = max(v['x'] for v in vertices)

        all_fields.append({
            'text': field['inferText'].strip(),
            'y_center': y_center,
            'x_start': x_start,
            'x_end': x_end,
            'x_center': (x_start + x_end) / 2
        })

    if not all_fields:
        return {"success": False, "error": "좌표(`boundingPoly`)가 포함된 V2 텍스트 필드를 찾을 수 없습니다."}

    all_fields.sort(key=lambda f: f['y_center'])

    # 2단계: 헤더 '기준점(Anchor)' 찾기
    y_header_counts = defaultdict(int)
    y_header_texts = defaultdict(list)
    header_y_tolerance = 10

    for field in all_fields:
        if field['text'] in HEADER_KEYWORDS:
            y_group = round(field['y_center'] / header_y_tolerance) * header_y_tolerance
            y_header_counts[y_group] += 1
            y_header_texts[y_group].append(field)

    if not y_header_counts:
        return {"success": False, "error": "테이블 헤더 키워드를 하나도 찾지 못했습니다."}

    best_y_group = max(y_header_counts, key=y_header_counts.get)
    header_line = sorted(y_header_texts[best_y_group], key=lambda f: f['x_center'])
    Y_HEADER = best_y_group

    expected_header_count = len(HEADER_KEYWORDS)
    found_header_count = len(header_line)

    if found_header_count != expected_header_count:
        error_msg = (f"필요한 헤더 {expected_header_count}개 중 {found_header_count}개만 감지되었습니다. "
                     f"감지된 헤더: {[f['text'] for f in header_line]}")
        return {"success": False, "error": error_msg}

    headers = [f['text'] for f in header_line]

    # 3단계: '타이트한' 열(Column) 경계(Bins) 설정
    header_x_centers = [f['x_center'] for f in header_line]
    column_bins = []
    for i, header_name in enumerate(headers):
        if i == 0:
            bin_start = header_line[i]['x_start'] - X_TOLERANCE
        else:
            bin_start = (header_x_centers[i - 1] + header_x_centers[i]) / 2

        if i == len(headers) - 1:
            bin_end = header_line[i]['x_end'] + X_TOLERANCE
        else:
            bin_end = (header_x_centers[i] + header_x_centers[i + 1]) / 2

        column_bins.append({'name': header_name, 'x_start': bin_start, 'x_end': bin_end})

    # 4단계: 스톱 '기준점(Anchor)' 찾기 (Padding 적용)
    Y_STOP = float('inf')
    for field in all_fields:
        if field['y_center'] > Y_HEADER + header_y_tolerance:
            if any(stop_word in field['text'] for stop_word in STOP_KEYWORDS):
                Y_STOP = field['y_center'] - Y_STOP_PADDING
                break

                # 5단계: Y좌표로 '진짜' 데이터 필터링 및 병합
    data_rows = []
    current_row_dict = {header: "" for header in headers}

    for field in all_fields:
        if (field['y_center'] > Y_HEADER + header_y_tolerance) and (field['y_center'] < Y_STOP):

            target_col_name = None
            for bin in column_bins:
                if (field['x_center'] >= bin['x_start']) and (field['x_center'] < bin['x_end']):
                    target_col_name = bin['name']
                    break

            if target_col_name:
                if current_row_dict[target_col_name]:
                    current_row_dict[target_col_name] += " " + field['text']
                else:
                    current_row_dict[target_col_name] = field['text']

    if any(current_row_dict.values()):
        data_rows.append(current_row_dict)

    # 6단계: [수정] 결과 return
    if not data_rows:
        return {"success": False, "error": "데이터 행을 재구성하지 못했습니다."}

    # 성공 시, 재구성된 데이터 행들의 리스트를 반환
    # 이 로직은 단 한 줄의 레코드를 추출합니다.
    # 만약 여러 줄을 추출해야 한다면 5단계 로직 수정이 필요합니다.
    # 현재 코드는 단일 행(첫 번째 행)만 반환합니다.
    return {"success": True, "data": data_rows}

def call_clova_ocr(image_file_path):
    """
    네이버 클로바 OCR API를 호출하여 이미지 내 템플릿 기반 텍스트를 추출하는 함수
    :param image_file_path: 분석할 이미지 파일의 경로
    :return: 성공 시 {"success": True, "data": parsed_data}, 실패 시 {"success": False, "error": ...}
    """
    request_body = {
        'version': 'V2',
        'requestId': str(uuid.uuid4()),
        'timestamp': int(round(time.time()) * 1000),
        'lang': 'ko',
        'images': [
            {
                'format': os.path.splitext(image_file_path)[1].lstrip('.').lower(),  # 파일 확장자 동적 추출
                'name': 'dorm_verification_general',
            }
        ],
        'enableTableDetection': False  # 좌표 기반 수동 파싱을 하므로 API의 테이블 감지 기능 끔
    }

    headers = {
        'X-OCR-SECRET': SECRET_KEY
    }

    try:
        # MIME 타입을 명시적으로 지정하는 방식으로 변경
        with open(image_file_path, 'rb') as f:
            file_format = request_body['images'][0]['format']
            if file_format == 'jpeg':
                file_format = 'jpg'
                request_body['images'][0]['format'] = 'jpg'

            file_mime_type = 'image/png' if file_format == 'png' else 'image/jpeg'

            files = {
                'file': (os.path.basename(image_file_path), f, file_mime_type),
                'message': (None, json.dumps(request_body), 'application/json')
            }

            response = requests.post(API_URL, headers=headers, files=files, timeout=10)
            response.raise_for_status()
            result = response.json()

        # 기존의 템플릿(`field.get('name')`) 기반 파싱 및 정규식 로직 전부 삭제

        # 새로운 좌표 기반 파싱 함수를 호출하고 그 결과를 바로 반환
        return process_ocr_response_with_coords(result)
        # ---------------------------

    except FileNotFoundError:
        return {"success": False, "error": f"파일을 찾을 수 없습니다: {image_file_path}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API 요청 중 오류 발생: {e}"}
    except Exception as e:
        return {"success": False, "error": f"알 수 없는 오류 발생: {e}"}