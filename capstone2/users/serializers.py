from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import User

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
