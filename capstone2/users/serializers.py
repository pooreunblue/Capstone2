import re
import os
import json
import uuid
from rest_framework import serializers
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework.validators import UniqueValidator

from users.models import User, DormInfo, Profile
from users.ocr_service import call_clova_ocr


class DormVerificationSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def validate(self, data):
        image = data.get('image')

        # 임시 파일 저장
        temp_file_name = f"ocr_temp_{uuid.uuid4()}.{image.name.split('.')[-1]}"
        temp_file_path = os.path.join(settings.MEDIA_ROOT, temp_file_name)

        try:
            path = default_storage.save(temp_file_path, image)
            full_temp_path = os.path.join(settings.MEDIA_ROOT, path)

            # OCR API 호출 (수정된 ocr_service 사용)
            ocr_result = call_clova_ocr(full_temp_path)

            if not ocr_result.get("success"):
                raise serializers.ValidationError(f"OCR API 실패: {ocr_result.get('error')}")

            ocr_data = ocr_result.get("data")  # ocr_data는 딕셔너리.

        finally:
            # 임시 파일 삭제 (기존 로직과 동일)
            if os.path.exists(full_temp_path):
                os.remove(full_temp_path)

        print("\n--- OCR 추출 결과 (딕셔너리 형태) ---")
        print(json.dumps(ocr_data, indent=4, ensure_ascii=False))
        print("---------------------------\n")

        # 새로운 한글 키로 Raw 텍스트 추출
        name = ocr_data.get("이름")
        student_id = ocr_data.get('학번')
        is_accepted_raw_text = ocr_data.get('합격여부', "")  # '합격여부' 전체 텍스트
        sex_text = ocr_data.get('성별', "")
        building_text = ocr_data.get('지원건물', "")
        room_text = ocr_data.get('지원호실구분', "")

        print(f"\n[DEBUG 1] 1차 검증: student_id '{student_id}' (타입: {type(student_id)})로 중복 검사 시작...")

        if not student_id or DormInfo.objects.filter(student_id=student_id).exists():
            print(f"[DEBUG 1] 중복 발견 또는 학번 없음!")
            raise serializers.ValidationError({"image": "이미 가입된 학번이거나, 학번을 인식할 수 없습니다."})

        print(f"[DEBUG 1] 중복 없음. 다음 단계 진행.")

        if not name:
            raise serializers.ValidationError("OCR 인식 실패: 이름을 찾을 수 없습니다.")

        # 정규식 파싱
        selected_semester = None
        semester_match = re.search(r'(\d{2}-\d학기)', is_accepted_raw_text)
        if semester_match:
            selected_semester = semester_match.group(1)

        is_accepted_text = "선발" if "선발" in is_accepted_raw_text else "미선발"

        period_text = ""
        period_match = re.search(r'\((학기|6개월)\)', is_accepted_raw_text)
        if period_match:
            period_text = period_match.group(1)

        # 선발 여부 확인
        if is_accepted_text != "선발":
            raise serializers.ValidationError({"image": "기숙사 선발 대상자가 아닙니다."})

        # Enum 변환
        sex_enum = "MALE" if sex_text == "남자" else "FEMALE"

        building_enum = None
        building_map = {"명덕관": "MYEONGDEOK", "명현관": "MYEONGHYEON", "3동": "DONG_3", "4동": "DONG_4", "5동": "DONG_5"}

        # '지원건물' 텍스트에서 괄호 제거 후 매핑 (혹은 'in'으로 확인)
        building_name_cleaned = building_text.split('(')[0].strip()

        for key, value in building_map.items():
            if key in building_name_cleaned:
                building_enum = value
                break

        if not building_enum:
            raise serializers.ValidationError(f"지원 건물을 인식할 수 없습니다: {building_text}")

        accepted_enum = "ACCEPTED"  # 이미 위에서 "선발"인지 검증했으므로
        room_enum = "QUAD" if room_text == "4인실" else "DOUBLE"
        period_enum = "SEMESTER" if period_text == "학기" else "SIXMONTHS"

        # 성별/건물 유효성 검사
        if sex_enum == "FEMALE" and building_enum == "DONG_3":
            raise serializers.ValidationError({"image": "여학생은 3동에 배정될 수 없습니다."})

        male_restricted = ['MYEONGHYEON', 'DONG_4', 'DONG_5']
        if sex_enum == "MALE" and building_enum in male_restricted:
            raise serializers.ValidationError({"image": "남학생은 해당 건물에 배정될 수 없습니다."})

        # 최종 데이터 반환
        validated_dorm_data = {
            "student_id": student_id,
            "selected_semester": selected_semester,
            "name": name,
            "sex": sex_enum,
            "building": building_enum,
            "is_accepted": accepted_enum,
            "room": room_enum,
            "residency_period": period_enum,
        }
        print(f"[DEBUG 2] 최종 저장될 데이터: {validated_dorm_data}\n")

        return validated_dorm_data

class SignUpSerializer(serializers.Serializer):
    nickname = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="중복된 닉네임 입니다. 다른 닉네임을 입력해주세요."
            )
        ]
    )
    application_order = serializers.CharField(required=False, allow_null=True)
    dorm_data = serializers.DictField(write_only=True, required=True)

    def create(self, validated_data):
        dorm_data = validated_data.pop('dorm_data')
        user = User.objects.create_user(
            nickname=validated_data['nickname'],
            application_order=validated_data.get('application_order'),
            password=None,
        )
        DormInfo.objects.create(user=user, **dorm_data)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='user.id', read_only=True)
    class Meta:
        model = Profile
        fields = [
            'student_id', 'age', 'grade', 'smoking_type', 'smoking_amount',
            'sleeping_habit', 'sleeping_habit_freq', 'sleeping_habit_extent',
            'life_style', 'wake_up_time', 'bed_time', 'pre_sleeping_life_style',
            'sensitivity_to_sleep', 'cleaning_cycle', 'eating_in_room'
        ]
        read_only_fields = ['student_id']
