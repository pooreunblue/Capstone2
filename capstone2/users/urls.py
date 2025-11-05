from django.urls import path

from users.views import SignUpView, DormVerificationView, ProfileView, MatchingFeedView, UserProfileDetailView, MyPageView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify-dorm/', DormVerificationView.as_view(), name='verify-dorm'),
    path('profile/', ProfileView.as_view(), name='profile'), # 초기 내 프로필 생성/수정
    path('matching/', MatchingFeedView.as_view(), name='matching-feed'),
    path('profile/<int:user_id>/', UserProfileDetailView.as_view(), name='user-profile-detail'), # 타인 프로필
    path('mypage/', MyPageView.as_view(), name='my-page'), # 마이페이지
]
