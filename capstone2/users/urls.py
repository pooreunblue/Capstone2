from django.urls import path

from config.urls import urlpatterns
from users.views import SignUpView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
]