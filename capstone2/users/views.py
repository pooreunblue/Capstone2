from datetime import datetime

import requests
from decouple import config
from django.conf import settings
from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import User, DormInfo, Profile
from .serializers import (
    DormVerificationSerializer, SignUpSerializer, ProfileSerializer,
    MatchingSummarySerializer, PublicProfileSerializer,
    MyUserSerializer, MyDormInfoSerializer, MyProfileSerializer, MessageSerializer)


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

        candidates_pool = User.objects.filter(
            dorminfo__sex=my_dorm_info.sex,
            dorminfo__building=my_dorm_info.building,
            dorminfo__room=my_dorm_info.room,
            dorminfo__residency_period=my_dorm_info.residency_period
        ).exclude(
            id=current_user.id  # 나 자신은 제외
        ).select_related('profile', 'dorminfo')  # DB 효율 최적화

        if not candidates_pool.exists():
            return Response([], status=status.HTTP_200_OK)  # 매칭 대상이 없으면 빈 리스트 반환

        # (데이터 준비) AI에게 보낼 'target'과 'candidates' 리스트 생성
        my_profile_data = ProfileSerializer(my_profile).data

        candidates_data = []
        for user in candidates_pool:
            if hasattr(user, 'profile'):
                candidates_data.append(ProfileSerializer(user.profile).data)

        # (AI 요청 데이터) AI 팀의 API 명세에 맞게 최종 요청 데이터 생성
        ai_request_data = {
            "target": my_profile_data,
            "candidates": candidates_data,
            "k": 10  # ⭐️ 상위 10명을 요청 (필요에 따라 조절)
        }

        # (AI 서버 주소) .env 파일에서 AI 서버 주소를 읽어옵니다.
        ai_url = config('AI_SERVER_URL') + '/v1/rank/topk'  # AI 팀이 알려준 엔드포인트

        ai_ordered_user_ids = []
        try:
            # (API 호출) AI 서버에 POST 요청을 보냅니다.
            response = requests.post(ai_url, json=ai_request_data, timeout=10)
            response.raise_for_status()  # 200번대가 아니면 에러 발생

            # (응답 파싱) AI 서버의 응답(JSON)을 파싱합니다.
            ai_response_data = response.json()

            # (ID 추출) 응답에서 추천 사용자 ID 목록을 추출합니다.
            results = ai_response_data.get('result', [])
            ai_ordered_user_ids = [item['candidate_id'] for item in results]  # [10, 12]

        except requests.exceptions.RequestException as e:
            # AI 서버가 다운되었거나 응답이 없는 경우
            return Response({"detail": f"매칭 서버와 통신 중 오류가 발생했습니다: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # AI 서버가 비정상적인 응답을 준 경우 (예: "ok": false)
            return Response({"detail": f"매칭 결과를 처리하는 중 오류가 발생했습니다: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 1차 필터링했던 후보자 리스트(candidates_pool)를 딕셔너리로 변환 (빠른 검색용)
        users_map = {user.id: user for user in candidates_pool}

        # AI가 정렬해준 ID 순서대로 User 객체 리스트를 재구성
        ordered_users = [users_map[user_id] for user_id in ai_ordered_user_ids if user_id in users_map]

        # 최종 결과 반환
        serializer = MatchingSummarySerializer(
            [user.profile for user in ordered_users if hasattr(user, 'profile')],
            many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserProfileDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Profile.objects.select_related('user').all()
    serializer_class = PublicProfileSerializer
    lookup_field = 'user_id'

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

class MessageSendView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        sender = get_user_from_header(self.request)
        if not sender:
            raise serializers.ValidationError("헤더에 유효한 X-User-ID가 없습니다.")

        recipient_id = self.request.data.get('recipient')
        if not recipient_id:
            raise serializers.ValidationError({"recipient": "받는 사람 ID가 필요합니다."})

        if str(sender.id) == str(recipient_id):
            raise serializers.ValidationError("자기 자신에게 쪽지를 보낼 수 없습니다.")

        serializer.save(sender=sender)