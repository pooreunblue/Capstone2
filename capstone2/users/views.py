from rest_framework import generics
from users.models import User
from users.serializers import UserSignUpSerializer

class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSignUpSerializer
