from django.urls import path

from users.views import SignUpView, DormVerificationView, ProfileView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify-dorm/', DormVerificationView.as_view(), name='verify-dorm'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
