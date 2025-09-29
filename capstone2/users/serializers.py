from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import User

class UserSignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="이미 사용 중인 아이디입니다. 다른 아이디를 입력해주세요.")
        ],
    )

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="이미 가입된 이메일입니다. 다른 이메일을 입력해주세요.")
        ]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
        }

    def createuser(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number', None)
        )
        return user
