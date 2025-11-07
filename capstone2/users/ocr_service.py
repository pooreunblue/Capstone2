from collections import defaultdict

import requests
import json
import uuid
import time
import os
from decouple import config

API_URL = config('CLOVA_OCR_APIGW_URL')
SECRET_KEY = config('CLOVA_OCR_SECRET_KEY')

HEADER_KEYWORDS = ['학번', '학년', '이름', '성별', '지원건물', '지원호실구분', '합격여부', '등록여부']
STOP_KEYWORDS = [
    'TEL.', 'FAX.', 'Copyright', 'All rights reserved',
    '개인정보처리', '이메일수집거부', '|<', 'K', '>|'
]
X_TOLERANCE = 20
Y_STOP_PADDING = 5
Y_DATA_MAX_HEIGHT = 400
HEADER_Y_TOLERANCE = 10

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

    if image['inferResult'] != 'SUCCESS'or 'fields' not in image or not image['fields']:
        return {"success": False, "error": "OCR 인식 실패 또는 텍스트 필드 없음"}

    # API 필드 정규화
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

    # 헤더 '기준점(Anchor)' 찾기
    y_header_counts = defaultdict(int)
    header_line_texts_map = defaultdict(list)

    for field in all_fields:
        if field['text'] in HEADER_KEYWORDS:
            y_group = round(field['y_center'] / HEADER_Y_TOLERANCE) * HEADER_Y_TOLERANCE
            y_header_counts[y_group] += 1
            header_line_texts_map[y_group].append(field)

    if not y_header_counts:
        return {"success": False, "error": f"테이블 헤더 키워드({len(HEADER_KEYWORDS)}개)를 하나도 찾지 못했습니다."}

    best_y_group = max(y_header_counts, key=y_header_counts.get)
    header_line = sorted(header_line_texts_map[best_y_group], key=lambda f: f['x_center'])
    Y_HEADER = best_y_group

    # 8개 헤더 검증
    expected_header_count = len(HEADER_KEYWORDS)
    found_header_count = len(header_line)

    if found_header_count != expected_header_count:
        error_msg = (f"필요한 헤더 {expected_header_count}개 중 {found_header_count}개만 감지되었습니다. "
                     f"감지된 헤더: {[f['text'] for f in header_line]}")
        return {"success": False, "error": error_msg}

    headers = [f['text'] for f in header_line]

    # 열(Column) 경계(Bins) 설정
    header_x_centers = [f['x_center'] for f in header_line]
    column_bins = []
    for i, header_name in enumerate(headers):
        bin_start = header_line[i]['x_start'] - X_TOLERANCE if i == 0 else (header_x_centers[i-1] + header_x_centers[i]) / 2
        bin_end = header_line[i]['x_end'] + X_TOLERANCE if i == len(headers) - 1 else (header_x_centers[i] + header_x_centers[i+1]) / 2
        column_bins.append({'name': header_name, 'x_start': bin_start, 'x_end': bin_end})

    # 스톱 '기준점(Anchor)' 찾기
    Y_STOP = float('inf')
    found_stop_keyword = False
    for field in all_fields:
        if (field['y_center'] > Y_HEADER + HEADER_Y_TOLERANCE) and any(stop_word in field['text'] for stop_word in STOP_KEYWORDS):
            Y_STOP = field['y_center'] - Y_STOP_PADDING
            found_stop_keyword = True
            break

    if not found_stop_keyword:
        Y_STOP = Y_HEADER + Y_DATA_MAX_HEIGHT

    # Y좌표로 데이터 필터링 및 병합
    data_rows = []
    current_row_dict = {header: "" for header in headers}

    for field in all_fields:
        if (field['y_center'] > Y_HEADER + HEADER_Y_TOLERANCE) and (field['y_center'] < Y_STOP):
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

    if not data_rows:
        return {"success": False, "error": "데이터 행을 재구성하지 못했습니다."}

    # 후처리 필터 (학년이 '-' 이면 빈칸으로)
    final_data_row = data_rows[0]
    if final_data_row.get('학년') == '-':
        final_data_row['학년'] = ''

    return {"success": True, "data": final_data_row} # ⭐️ 리스트가 아닌 딕셔너리(첫 번째 행) 반환

def call_clova_ocr(image_file_path):
    """
    네이버 클로바 'General OCR' API를 호출하고, AI 팀의 파싱 로직을 실행하는 함수.
    """
    message = {
        'version': 'V2',
        'requestId': str(uuid.uuid4()),
        'timestamp': int(round(time.time() * 1000)),
        'lang': 'ko',
        'images': [
            {
                'format': os.path.splitext(image_file_path)[1].lstrip('.').lower(),
                'name': 'dorm_verification_image'
            }
        ],
        'enableTableDetection': False
    }

    headers = {
        'X-OCR-SECRET': SECRET_KEY
    }

    try:
        with open(image_file_path, 'rb') as f:
            file_format = message['images'][0]['format']
            file_mime_type = 'image/png' if file_format == 'png' else 'image/jpeg'

            files = {
                'file': (os.path.basename(image_file_path), f, file_mime_type),
                'message': (None, json.dumps(message), 'application/json')
            }

            response = requests.post(API_URL, headers=headers, files=files, timeout=10)
            response.raise_for_status()
            result = response.json()

        return process_ocr_response_with_coords(result)

    except FileNotFoundError:
        return {"success": False, "error": f"파일을 찾을 수 없습니다: {image_file_path}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API 요청 중 오류 발생: {e}"}
    except Exception as e:
        return {"success": False, "error": f"알 수 없는 오류 발생: {e}"}
