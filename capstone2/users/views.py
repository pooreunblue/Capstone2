import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, DormInfo, Profile
from .serializers import DormVerificationSerializer, SignUpSerializer, ProfileSerializer

class DormVerificationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = DormVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dorm_data = serializer.validated_data['validated_dorm_data']
        payload = {
            'dorm_data': dorm_data,
            'exp': datetime.utcnow() + timedelta(minutes=60)
        }
        verification_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return Response({"verification_token": verification_token}, status=status.HTTP_200_OK)

class SignUpView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data.get('verification_token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            dorm_data = payload.get('dorm_data')
            user = serializer.save(dorm_data=dorm_data)  # create 메서드에 dorm_data 전달
            refresh = RefreshToken.for_user(user)
            return Response({
                "user_id": user.id, "nickname": user.nickname,
                "tokens": {'refresh': str(refresh), 'access': str(refresh.access_token)}
            }, status=status.HTTP_201_CREATED)
        except jwt.ExpiredSignatureError:
            return Response({"detail": "인증 시간이 만료되었습니다. 다시 시도해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({"detail": "유효하지 않은 인증 토큰입니다."}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile