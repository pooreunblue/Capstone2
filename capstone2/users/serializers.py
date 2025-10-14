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
        current_semester = "25-2학기"

        if not student_id or DormInfo.objects.filter(student_id=student_id).exists():
            raise serializers.ValidationError("이미 가입된 학번이거나, 학번을 인식할 수 없습니다.")

        if selected_semester != current_semester:
            raise serializers.ValidationError("현재 학기 합격자 조회결과가 아닙니다.")

        if is_accepted_text != "선발":
            raise serializers.ValidationError("기숙사 선발 대상자가 아닙니다.")

        sex_enum = "MALE" if sex_text == "남자" else "FEMALE"
        if building_text == "명덕관":
            building_enum = "MYEONGDEOK"
        elif building_text == "명현관":
            building_enum = "MYEONGHYEON"
        elif building_text == "3동":
            building_enum = "DONG_3"
        elif building_text == "4동":
            building_enum = "DONG_4"
        elif building_text == "5동":
            building_enum = "DONG_5"
        else:
            raise serializers.ValidationError(f"지원 건물을 인식할 수 없습니다: {building_text}")
        accepted_enum = "ACCEPTED" if is_accepted_text == "선발" else "NOT_ACCEPTED"
        room_enum = "QUAD" if room_text == "4인실" else "DOUBLE"
        period_enum = "SEMESTER" if period_text == "학기" else "SIXMONTHS"

        if sex_enum == "FEMALE" and building_enum == "DONG_3":
            raise serializers.ValidationError("여학생은 3동에 배정될 수 없습니다.")

        male_restricted = ['MYEONGHYEON', 'DONG_4', 'DONG_5']
        if sex_enum == "MALE" and building_enum in male_restricted:
            raise serializers.ValidationError("남학생은" + building_text + "에 배정될 수 없습니다.")

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
        data['validated_dorm_data'] = validated_dorm_data
        return data

class SignUpSerializer(serializers.Serializer):
    verification_token = serializers.CharField(required=True)
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

    def create(self, validated_data):
        dorm_data = validated_data.pop('dorm_data')
        user = User.objects.create(
            nickname=validated_data['nickname'],
            application_order=validated_data.get('application_order'),
        )
        user.set_unusable_password()
        user.save()
        DormInfo.objects.create(user=user, **dorm_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ('user',)
