from django.urls import path

from users.views import SignUpView, DormVerificationView, ProfileView, MatchingFeedView, UserProfileDetailView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify-dorm/', DormVerificationView.as_view(), name='verify-dorm'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('matching/', MatchingFeedView.as_view(), name='matching-feed'),
    path('profile/<int:user_id>/', UserProfileDetailView.as_view(), name='user-profile-detail'),
]
