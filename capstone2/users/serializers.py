from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import User, DormInfo, Profile


class UserSignUpSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해주세요.")
        ],
    )

    class Meta:
        model = User
        fields = ['nickname', 'age']

    def create(self, validated_data):
        user = User.objects.create(
            nickname=validated_data['nickname'],
            age=validated_data.get('age')
        )
        user.set_unusable_password()
        user.save()
        return user

class DormInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DormInfo
        fields = ['name', 'sex', 'application_order', 'building', 'room', 'residency_period', 'is_accepted']

    def validate(self, data):
        sex = data.get('sex')
        building = data.get('building')
        if sex == DormInfo.SexChoices.FEMALE and building == DormInfo.BuildingChoices.DONG_3:
            raise serializers.ValidationError(
                {"building": "여학생은 3동에 배정될 수 없습니다."}
            )
        male_restricted_buildings = [
            DormInfo.BuildingChoices.MYEONGHYEON,
            DormInfo.BuildingChoices.DONG_4,
            DormInfo.BuildingChoices.DONG_5,
        ]
        if sex == DormInfo.SexChoices.MALE and building in male_restricted_buildings:
            raise serializers.ValidationError(
                {"building": "남학생은" + building + "에 배정될 수 없습니다."}
            )
        if data.get('is_accepted') != DormInfo.AcceptanceChoices.ACCEPTED:
            raise serializers.ValidationError({"is_accepted": "기숙사 선발 정보가 확인되지 않습니다."})
        return data

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ('user',)

class DormVerificationSerializer(serializers.Serializer):
    image = serializers.ImageField(required=False)