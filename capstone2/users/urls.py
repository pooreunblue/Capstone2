from django.urls import path

from users.views import SignUpView, DormInfoView, ProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('dorminfo/', DormInfoView.as_view(), name='dorm-info'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
