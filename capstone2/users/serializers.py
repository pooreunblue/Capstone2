import os
import uuid

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import User, DormInfo, Profile
from users.ocr_service import call_clova_ocr

class DormVerificationSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

    def validate(self, data):
        image_file = data['image']
        temp_file_path = f'temp_{uuid.uuid4()}.jpg'
        with open(temp_file_path, 'wb+') as temp_file:
            for chunk in image_file.chunks():
                temp_file.write(chunk)
        try:
            ocr_result = call_clova_ocr(temp_file_path)
            if not ocr_result.get("success"):
                raise serializers.ValidationError({"image": f"OCR 처리 중 오류: {ocr_result.get('error')}"})
            ocr_data = ocr_result.get("data", {})
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        name = ocr_data.get("name")
        student_id = ocr_data.get('student_id')
        selected_semester = ocr_data.get('selected_semester')
        is_accepted_text = ocr_data.get('is_accepted')
        sex_text = ocr_data.get('gender')
        building_text = ocr_data.get('dormitory_name', "")
        room_text = ocr_data.get('room_type', "")
        period_text = ocr_data.get('residency_period')
        current_semester = "25-1학기"

        if not student_id or DormInfo.objects.filter(student_id=student_id).exists():
            raise serializers.ValidationError({"image":"이미 가입된 학번이거나, 학번을 인식할 수 없습니다."})

        if selected_semester != current_semester:
            raise serializers.ValidationError({"image":"현재 학기 합격자 조회 결과가 아닙니다."})

        if is_accepted_text != "선발":
            raise serializers.ValidationError({"image":"기숙사 선발 대상자가 아닙니다."})

        sex_enum = "MALE" if sex_text == "남자" else "FEMALE"
        building_enum = None
        building_map = {"명덕관": "MYEONGDEOK", "명현관": "MYEONGHYEON", "3동": "DONG_3", "4동": "DONG_4", "5동": "DONG_5"}
        for key, value in building_map.items():
            if key in building_text:
                building_enum = value
                break
        if not building_enum:
            raise serializers.ValidationError(f"지원 건물을 인식할 수 없습니다: {building_text}")

        accepted_enum = "ACCEPTED" if is_accepted_text == "선발" else "NOT_ACCEPTED"
        room_enum = "QUAD" if room_text == "4인실" else "DOUBLE"
        period_enum = "SEMESTER" if period_text == "학기" else "SIXMONTHS"

        if sex_enum == "FEMALE" and building_enum == "DONG_3":
            raise serializers.ValidationError({"image":"여학생은 3동에 배정될 수 없습니다."})

        male_restricted = ['MYEONGHYEON', 'DONG_4', 'DONG_5']
        if sex_enum == "MALE" and building_enum in male_restricted:
            raise serializers.ValidationError({"image":"남학생은 해당 건물에 배정될 수 없습니다."})

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
    class Meta:
        model = Profile
        exclude = ('user',)
