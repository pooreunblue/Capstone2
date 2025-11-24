import requests
from decouple import config
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView

from users.models import User, DormInfo, Profile
from users.serializers import ProfileSerializer, MatchingSummarySerializer, PublicProfileSerializer
from users.utils import get_user_from_header
from django.core.paginator import Paginator, EmptyPage

class MatchingFeedView(APIView):
    permission_classes = [AllowAny]
    ITEMS_PER_PAGE = 5

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

        try:
            page_number = int(request.query_params.get('page', 1))
        except ValueError:
            page_number = 1

        candidates_pool = User.objects.filter(
            dorminfo__sex=my_dorm_info.sex,
            dorminfo__building=my_dorm_info.building,
            dorminfo__room=my_dorm_info.room,
            dorminfo__residency_period=my_dorm_info.residency_period
        ).exclude(
            id=current_user.id  # 나 자신은 제외
        ).select_related('profile', 'dorminfo')  # DB 효율 최적화

        if not candidates_pool.exists():
            return Response({
                "results": [],
                "next_page": None,
                "has_next": False
            }, status=status.HTTP_200_OK)  # 매칭 대상이 없으면 빈 리스트 반환

        # (데이터 준비) AI에게 보낼 'target'과 'candidates' 리스트 생성
        my_profile_data = ProfileSerializer(my_profile).data

        candidates_data = []
        MAX_CANDIDATES_REQUEST = 50
        for user in candidates_pool:
            if hasattr(user, 'profile'):
                candidates_data.append(ProfileSerializer(user.profile).data)

        # (AI 요청 데이터) AI 팀의 API 명세에 맞게 최종 요청 데이터 생성
        ai_request_data = {
            "target": my_profile_data,
            "candidates": candidates_data,
            "k": MAX_CANDIDATES_REQUEST
        }

        ai_url = config('AI_SERVER_URL') + '/v1/rank/topk'

        ai_api_key = config('AI_API_KEY')
        ai_headers = {
            'x-api-key': ai_api_key
        }

        ai_ordered_user_ids = []
        ai_match_data = {}

        try:
            # (API 호출)
            response = requests.post(ai_url, json=ai_request_data, headers=ai_headers, timeout=20)
            response.raise_for_status()

            # (응답 파싱)
            ai_response_data = response.json()

            # (ID 추출)
            results = ai_response_data.get('result', [])
            for item in results:
                user_id = item['candidate_id']
                match_percent = item.get('match_percent')  # .get()으로 안전하게 접근

                ai_ordered_user_ids.append(user_id)
                if match_percent is not None:
                    ai_match_data[user_id] = match_percent

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

        paginator = Paginator(ordered_users, self.ITEMS_PER_PAGE)
        target_page_number = page_number
        try:
            # 현재 페이지의 유저 객체 목록을 가져옴 (예: 6번째~10번째 유저)
            page_obj = paginator.page(target_page_number)

        except EmptyPage:
            if paginator.num_pages >= 1:
                target_page_number = 1
                page_obj = paginator.page(target_page_number)
            else:
                # 데이터가 아예 없을 때 (num_pages가 0일 때)
                return Response({"detail": f"매칭 결과가 없습니다.", "results": [], "next_page": None, "has_next": False}, status=status.HTTP_200_OK)

        paginated_users = page_obj.object_list
        serializer_context = {
            'ai_match_data': ai_match_data
        }

        # 최종 결과 반환
        serializer = MatchingSummarySerializer(
            [user.profile for user in paginated_users if hasattr(user, 'profile')],
            many=True,
            context=serializer_context
        )
        is_last_page = (target_page_number == paginator.num_pages)
        next_page_return = 1 if is_last_page else target_page_number + 1
        return Response({
            "results": serializer.data,
            "next_page": next_page_return,
            "has_next": True if paginator.num_pages > 1 else False
        }, status=status.HTTP_200_OK)

class UserProfileDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Profile.objects.select_related('user').all()
    serializer_class = PublicProfileSerializer
    lookup_field = 'user_id'
