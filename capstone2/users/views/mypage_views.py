from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Profile, DormInfo
from users.serializers.mypage_serializers import MyUserSerializer, MyDormInfoSerializer, MyProfileSerializer
from users.utils import get_user_from_header


class MyPageView(APIView):
    permission_classes = [AllowAny]  # X-User-ID 헤더로 인증

    def get(self, request, *args, **kwargs):
        user = get_user_from_header(request)
        if not user:
            return Response(
                {"detail": "헤더에 유효한 X-User-ID가 없습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # 1. DB에서 '나'의 모든 정보를 한 번에 JOIN
            profile = Profile.objects.select_related('user', 'user__dorminfo').get(user=user)
            user_instance = profile.user
            dorm_instance = user_instance.dorminfo

            # 2. 3개의 '읽기 전용' Serializer로 각각 조합
            response_data = {
                "user_info": MyUserSerializer(user_instance).data,
                "dorm_info": MyDormInfoSerializer(dorm_instance).data,
                "profile_info": MyProfileSerializer(profile).data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except (Profile.DoesNotExist, DormInfo.DoesNotExist):
            return Response(
                {"detail": "프로필 또는 기숙사 정보가 등록되지 않았습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"detail": f"오류 발생: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)