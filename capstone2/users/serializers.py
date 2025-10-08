from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import User, DormInfo, Profile


class UserSignUpSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="이미 사용 중인 아이디입니다.")
        ],
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="이미 가입된 이메일입니다.")
        ]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'phone_number']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number', None)
        )
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

class DormAcceptImageSerializer(serializers.Serializer):
    image = serializers.ImageField()