import os
import uuid

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import User, DormInfo, Profile
from users.ocr_service import call_clova_ocr

class DormVerificationSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = DormInfo
        fields = ['name', 'student_id','sex', 'application_order', 'building', 'room', 'residency_period', 'selected_semester', 'is_accepted']

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

        sex = data.get('sex')
        student_id = data.get('student_id')
        building = data.get('building')
        selected_semester = data.get('selected_semester')
        is_accepted = data.get('is_accepted')
        current_semester = "2025-2학기"

        if sex == DormInfo.SexChoices.FEMALE and building == DormInfo.BuildingChoices.DONG_3:
            raise serializers.ValidationError("여학생은 3동에 배정될 수 없습니다.")

        male_restricted = ['MYEONGHYEON', 'DONG_4', 'DONG_5']
        if sex == DormInfo.SexChoices.MALE and building in male_restricted:
            raise serializers.ValidationError("남학생은" + building + "에 배정될 수 없습니다.")

        if not student_id or DormInfo.objects.filter(student_id=student_id).exists():
            raise serializers.ValidationError("이미 가입된 학번이거나, 학번을 인식할 수 없습니다.")

        if selected_semester != self.current_semester:
            raise serializers.ValidationError("현재 학기 합자 조회결과 입니다.")

        if data.get('is_accepted') != DormInfo.AcceptanceChoices.ACCEPTED:
            raise serializers.ValidationError("기숙사 선발 대상자가 아닙니다.")
        return data


class SignUpSerializer(serializers.Serializer):
    """
    2단계: 임시 인증 토큰과 닉네임, 나이를 받아 최종 가입을 처리하는 Serializer.
    """
    # 안드로이드 앱으로부터 받을 데이터 필드를 정의합니다.
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
    age = serializers.IntegerField(required=False, allow_null=True)

    def create(self, validated_data):
        # View에서 전달받은 OCR 데이터를 사용하여 User와 DormInfo를 생성합니다.
        dorm_data = validated_data.pop('dorm_data')

        # User 객체 생성
        user = User.objects.create(
            nickname=validated_data['nickname'],
            age=validated_data.get('age')
        )
        user.set_unusable_password()
        user.save()

        # DormInfo 객체 생성 및 User와 연결
        DormInfo.objects.create(user=user, **dorm_data)

        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ('user',)
