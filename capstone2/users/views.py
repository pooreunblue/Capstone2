from datetime import datetime
from django.conf import settings
from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import User, DormInfo, Profile
from .serializers import DormVerificationSerializer, SignUpSerializer, ProfileSerializer

def get_user_from_header(request):
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    try:
        user_id = int(user_id)
        return User.objects.get(id=user_id)
    except (ValueError, User.DoesNotExist):
        return None

class DormVerificationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = DormVerificationSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignUpView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user_id": user.id,
                "nickname": user.nickname,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    def get_object(self):
        user = get_user_from_header(self.request)
        if not user:
            raise serializers.ValidationError("헤더에 유효한 X-User-ID가 없습니다.")
        profile, created = Profile.objects.get_or_create(user=user)
        return profile

class MatchingFeedView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        current_user = get_user_from_header(request)
        if not current_user:
                return Response({"detail": "헤더에 유효한 X-User-ID가 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            my_profile = current_user.profile
            my_dorm_info = current_user.dorminfo
        except (Profile.DoesNotExist, DormInfo.DoesNotExist):
            return Response(
                {"프로필 또는 기숙사 정보가 등록되지 않았습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- AI 서버와 연동 부분 ---
        #    AI 서버로 내 프로필 정보를 보내고, 유사도 순으로 정렬된 사용자 ID 리스트를 받음.
        #    (API 명세에 따라 requests.post() 등으로 구현)
        #    [AI 서버에 보낼 데이터 예시]
        #    my_profile_data = ProfileSerializer(my_profile).data
        #    ai_response = requests.post("http://AI서버주소/match", json=my_profile_data)
        #    ai_recommended_user_ids = ai_response.json().get("user_ids")

        #    아래와 같이 더미 데이터로 시뮬레이션.
        ai_recommended_user_ids = [5, 12, 3, 8, 2]

        matching_pool = User.objects.filter(
            id__in=ai_recommended_user_ids,
            dorminfo__sex=my_dorm_info.sex,
            dorminfo__building=my_dorm_info.building,
            dorminfo__room=my_dorm_info.room,
            dorminfo__residency_period=my_dorm_info.residency_period
        ).exclude(
            id=current_user.id  # 나 자신은 제외
        )

        serializer = ProfileSerializer(
            [user.profile for user in matching_pool if hasattr(user, 'profile')], # 객체가 특정 속성 가지고 있는지 확인
            many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)